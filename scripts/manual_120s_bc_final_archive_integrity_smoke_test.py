from __future__ import annotations

import argparse
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.demo_contract import (  # noqa: E402
    DEFAULT_DEMO_PATH,
    DIRECT_ACTION_MANIFEST_SHA256,
    SOURCE_ROUTE_FILE_SHA256,
    bytes_sha256,
    file_sha256,
)


DEFAULT_ARCHIVE = ROOT.parent / "ww-dps-simulator-2-111.zip"
EXPECTED_BC_MODEL_SHA256 = "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e"
EXPECTED_PPO_MODEL_SHA256 = "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513"
EXPECTED_EVAL_SELECTED_SEQUENCE_SHA256 = "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
EXPECTED_EVAL_RESOLVED_SEQUENCE_SHA256 = "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
EXPECTED_EVAL_TOTAL_DAMAGE = 5165134.682363356
EXPECTED_EVAL_DPS = 43042.78901969464
EXPECTED_SCHEDULED_DAMAGE = 205987.4042873791
EXPECTED_DAMAGE_BY_CHARACTER = {
    "aemeath": 3733934.8538652016,
    "mornye": 268807.92005964793,
    "lynae": 1162391.9084385103,
}
EXPECTED_PPO_SELECTED_SEQUENCE_SHA256 = "0bba8688b3a085fde3a842901f659b24fdefd009102cc1ccba5a0d971a27c11d"
EXPECTED_PPO_RESOLVED_SEQUENCE_SHA256 = "9650b6e4d1b8f9ba616c26293f60c8cc4a5d6ea57dcf7153305aa085f84ad6e1"
EXPECTED_PPO_TOTAL_DAMAGE = 3600637.129626801
EXPECTED_PPO_DPS = 30005.309413556675
EXPECTED_PPO_SCHEDULED_DAMAGE = 140026.5111366104
EXPECTED_BEAM_PLAN_SHA256 = "b504def4e0c1da82ef2a6024d19ccac76fe175df51899e50d12f3bff99a17998"
EXPECTED_PPO_DAMAGE_BY_CHARACTER = {
    "aemeath": 2674131.053725695,
    "mornye": 201528.93426401448,
    "lynae": 724977.1416370921,
}
REQUIRED_FILES = (
    "PROJECT_PROGRESS_STATE.json",
    "data/manual_120s_baseline_routes_v104.json",
    "data/generated/manual_120s_bc_demonstration_v105.npz",
    "results/manual_120s_bc_demonstration_v105_summary.json",
    "results/ppo_evaluation_summary.json",
    "results/ppo_timeline.csv",
    "results/ppo_100k_evaluation_summary.json",
    "results/ppo_100k_timeline.csv",
    "results/manual_bc_ppo_comparison_v108.json",
    "results/training_metadata.json",
    "data/guarded_ppo_experiment_plan_v109.json",
    "results/guarded_ppo_v109/experiment_state.json",
    "results/guarded_ppo_v109/leaderboard.json",
    "results/guarded_ppo_v109/best_checkpoint.json",
    "results/guarded_ppo_v109/final_experiment_summary.json",
    "reports/manual_120s_bc_demonstration_v105.md",
    "reports/guarded_ppo_experiment_v109.md",
    "reports/guarded_ppo_experiment_v109_results.md",
    "reports/beam_search_v111.md",
    "data/beam_search_plan_v111.json",
    "models/maskable_ppo_bc_v105.zip",
    "models/maskable_ppo_bc_v105.zip.bc_metadata.json",
    "models/maskable_ppo_candidate_after_bc_v105.zip",
    "models/maskable_ppo_candidate_after_bc_v105.zip.ppo_metadata.json",
    "rl/damage_attribution.py",
    "rl/demo_contract.py",
    "rl/evaluation_report.py",
    "rl/evaluate_maskable_ppo.py",
    "rl/guarded_ppo.py",
    "rl/run_guarded_ppo_experiment.py",
    "rl/train_maskable_ppo.py",
    "rl/pretrain_maskable_ppo_bc.py",
    "search/__init__.py",
    "search/beam_plan.py",
    "search/beam_reporting.py",
    "search/beam_search.py",
    "search/beam_state.py",
    "search/run_beam_search.py",
    "scripts/manual_120s_bc_demo_contract_smoke_test.py",
    "scripts/manual_120s_bc_packaged_generation_parity_smoke_test.py",
    "scripts/manual_120s_bc_report_portability_smoke_test.py",
    "scripts/bc_pretrain_evaluator_contract_smoke_test.py",
    "scripts/evaluate_bc_sidecar_compatibility_smoke_test.py",
    "scripts/pretrain_bc_initial_active_contract_smoke_test.py",
    "scripts/project_progress_active_echo_alignment_smoke_test.py",
    "scripts/project_progress_manual_120s_baseline_alignment_smoke_test.py",
    "scripts/project_progress_bc_demo_alignment_smoke_test.py",
    "scripts/project_progress_ppo_100k_alignment_smoke_test.py",
    "scripts/project_progress_guarded_ppo_alignment_smoke_test.py",
    "scripts/project_progress_guarded_ppo_results_alignment_smoke_test.py",
    "scripts/evaluation_event_source_damage_attribution_smoke_test.py",
    "scripts/evaluation_scheduled_damage_role_breakdown_smoke_test.py",
    "scripts/bc_evaluation_manual_baseline_parity_smoke_test.py",
    "scripts/ppo_100k_evaluation_contract_smoke_test.py",
    "scripts/manual_bc_ppo_comparison_smoke_test.py",
    "scripts/ingest_guarded_ppo_v109_completed_experiment.py",
    "scripts/guarded_ppo_plan_contract_smoke_test.py",
    "scripts/guarded_ppo_branch_continuation_smoke_test.py",
    "scripts/guarded_ppo_damage_only_objective_smoke_test.py",
    "scripts/guarded_ppo_scratch_control_smoke_test.py",
    "scripts/guarded_ppo_resume_smoke_test.py",
    "scripts/guarded_ppo_cli_execution_gate_smoke_test.py",
    "scripts/guarded_ppo_seed_contract_smoke_test.py",
    "scripts/guarded_ppo_incumbent_best_retention_smoke_test.py",
    "scripts/guarded_ppo_failure_resume_smoke_test.py",
    "scripts/guarded_ppo_orphan_checkpoint_adoption_smoke_test.py",
    "scripts/guarded_ppo_state_integrity_smoke_test.py",
    "scripts/guarded_ppo_route_diagnostics_smoke_test.py",
    "scripts/guarded_ppo_stage_timeout_smoke_test.py",
    "scripts/guarded_ppo_cross_platform_path_canonicalization_smoke_test.py",
    "scripts/guarded_ppo_checkpoint_sidecar_strict_contract_smoke_test.py",
    "scripts/guarded_ppo_completed_experiment_integrity_smoke_test.py",
    "scripts/guarded_ppo_completed_experiment_spot_evaluation_smoke_test.py",
    "scripts/guarded_ppo_route_similarity_diagnostic_only_smoke_test.py",
    "scripts/guarded_ppo_dry_run_step0_alias_smoke_test.py",
    "scripts/ppo_checkpoint_sidecar_smoke_test.py",
    "scripts/guarded_ppo_short_integration_smoke_test.py",
    "scripts/build_candidate_archive_output_guard_smoke_test.py",
    "scripts/beam_search_plan_contract_smoke_test.py",
    "scripts/beam_search_clone_isolation_smoke_test.py",
    "scripts/beam_search_clone_behavioral_parity_smoke_test.py",
    "scripts/beam_search_state_roundtrip_smoke_test.py",
    "scripts/beam_search_state_fingerprint_contract_smoke_test.py",
    "scripts/beam_search_state_payload_size_smoke_test.py",
    "scripts/beam_search_exact_dedup_dominance_smoke_test.py",
    "scripts/beam_search_true_time_bucket_smoke_test.py",
    "scripts/beam_search_legal_action_expansion_smoke_test.py",
    "scripts/beam_search_zero_time_action_smoke_test.py",
    "scripts/beam_search_cutoff_scheduler_smoke_test.py",
    "scripts/beam_search_delayed_payoff_diversity_smoke_test.py",
    "scripts/beam_search_real_diversity_key_contract_smoke_test.py",
    "scripts/beam_search_damage_only_winner_smoke_test.py",
    "scripts/beam_search_manual_route_independence_guard_smoke_test.py",
    "scripts/beam_search_resume_integrity_smoke_test.py",
    "scripts/beam_search_resume_equivalence_smoke_test.py",
    "scripts/beam_search_realistic_2000_resume_equivalence_smoke_test.py",
    "scripts/beam_search_hot_path_scalability_smoke_test.py",
    "scripts/beam_search_checkpoint_interval_smoke_test.py",
    "scripts/beam_search_route_store_compaction_smoke_test.py",
    "scripts/beam_search_diversity_phase_contract_smoke_test.py",
    "scripts/beam_search_future_field_classification_smoke_test.py",
    "scripts/beam_search_short_window_diversity_smoke_test.py",
    "scripts/beam_search_horizon_comparison_guard_smoke_test.py",
    "scripts/beam_search_pending_frontier_bound_smoke_test.py",
    "scripts/beam_search_peak_live_metric_smoke_test.py",
    "scripts/beam_search_intra_bucket_budget_guard_smoke_test.py",
    "scripts/beam_search_partial_node_resume_smoke_test.py",
    "scripts/beam_search_final_replay_reporting_smoke_test.py",
    "scripts/beam_search_terminal_replay_parity_smoke_test.py",
    "scripts/beam_search_completed_route_reporting_contract_smoke_test.py",
    "scripts/beam_search_completion_order_smoke_test.py",
    "scripts/beam_search_memory_bound_contract_smoke_test.py",
    "scripts/beam_search_destination_bucket_test_utils.py",
    "scripts/beam_search_destination_accumulator_hot_path_smoke_test.py",
    "scripts/beam_search_destination_accumulator_spill_smoke_test.py",
    "scripts/beam_search_destination_accumulator_manifest_size_smoke_test.py",
    "scripts/beam_search_compact_cli_output_smoke_test.py",
    "scripts/beam_search_accumulator_metrics_contract_smoke_test.py",
    "scripts/beam_search_duplicate_lineage_tie_smoke_test.py",
    "scripts/beam_search_destination_bucket_order_independence_smoke_test.py",
    "scripts/beam_search_destination_bucket_batch_equivalence_smoke_test.py",
    "scripts/beam_search_destination_bucket_partition_merge_smoke_test.py",
    "scripts/beam_search_destination_bucket_resume_equivalence_smoke_test.py",
    "scripts/beam_search_diversity_quota_fill_smoke_test.py",
    "scripts/beam_search_cli_execution_gate_smoke_test.py",
    "scripts/beam_search_bounded_integration_smoke_test.py",
    "scripts/project_progress_beam_search_alignment_smoke_test.py",
)
EXPECTED_GUARDED_PLAN_SHA256 = "0306c734347e49460fd7273bce546eed80a2db657e460eb707f5cab961a9e0e6"
TEXT_SUFFIXES = (".py", ".json", ".md", ".txt")
AUTHORITATIVE_SOURCE_FILES = (
    "data/actions.json",
    "direct_action_data_patch_manifest_v61.json",
    "data/source/direct_action_data_patch_manifest_v61.json",
)
CORRECT_SHEET_NAME = "".join(chr(codepoint) for codepoint in (0x58F0, 0x9AB8))
FORBIDDEN_CORRUPTED_SHEET_NAME = "".join(chr(codepoint) for codepoint in (0x9DAF, 0xACC8, 0x3058))
ESTABLISHED_MOJIBAKE_MARKERS = (
    "".join(chr(codepoint) for codepoint in (0x00EF, 0x00BB, 0x00BF)),
    "".join(chr(codepoint) for codepoint in (0x00E9, 0x00B6, 0x00AF, 0x00EA, 0x00B3, 0x02C6, 0x00EC, 0x00A7)),
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    stats = validate_archive(args.archive)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print("manual_120s_bc_final_archive_integrity_smoke_test ok")


def validate_archive(archive: Path) -> dict[str, Any]:
    assert archive.exists(), archive
    with zipfile.ZipFile(archive) as zf:
        names = [info.filename for info in zf.infolist()]
        name_set = set(names)
        for required in REQUIRED_FILES:
            assert required in name_set, required
        cache_entries = [name for name in names if _is_cache_entry(name)]
        obsolete_bundle_entries = [
            name for name in names if name.replace("\\", "/") == "bc_eval_bundle/" or name.startswith("bc_eval_bundle/")
        ]
        assert not cache_entries, cache_entries[:20]
        assert not obsolete_bundle_entries, obsolete_bundle_entries

        route_bytes = zf.read("data/manual_120s_baseline_routes_v104.json")
        assert bytes_sha256(route_bytes) == SOURCE_ROUTE_FILE_SHA256
        _assert_json(zf.read("data/manual_120s_baseline_routes_v104.json"))

        summary = json.loads(zf.read("results/manual_120s_bc_demonstration_v105_summary.json").decode("utf-8"))
        evaluation_summary = json.loads(zf.read("results/ppo_evaluation_summary.json").decode("utf-8"))
        ppo_summary = json.loads(zf.read("results/ppo_100k_evaluation_summary.json").decode("utf-8"))
        comparison = json.loads(zf.read("results/manual_bc_ppo_comparison_v108.json").decode("utf-8"))
        progress = json.loads(zf.read("PROJECT_PROGRESS_STATE.json").decode("utf-8"))
        guarded_plan_bytes = zf.read("data/guarded_ppo_experiment_plan_v109.json")
        assert bytes_sha256(guarded_plan_bytes) == EXPECTED_GUARDED_PLAN_SHA256
        guarded_plan = json.loads(guarded_plan_bytes.decode("utf-8"))
        assert guarded_plan["schema_version"] == "guarded_ppo_experiment_plan_v109"
        assert [branch["branch_id"] for branch in guarded_plan["branches"]] == [
            "bc_conservative_seed_11",
            "bc_exploratory_seed_73",
            "scratch_control_seed_137",
        ]
        beam_plan_bytes = zf.read("data/beam_search_plan_v111.json")
        assert bytes_sha256(beam_plan_bytes) == EXPECTED_BEAM_PLAN_SHA256
        beam_plan = json.loads(beam_plan_bytes.decode("utf-8"))
        assert beam_plan["schema_version"] == "beam_search_plan_v111"
        assert beam_plan["candidate"] == "111"
        assert beam_plan["execution_boundary"]["candidate_111_runs_calibration"] is False
        assert beam_plan["execution_boundary"]["candidate_111_runs_full_search"] is False
        assert beam_plan["execution_boundary"]["candidate_111_runs_mcts"] is False
        assert beam_plan["execution_boundary"]["smoke_max_combat_duration"] == 3.0
        assert beam_plan["execution_boundary"]["smoke_max_expansions"] == 2000
        assert beam_plan["memory_estimate_contract"]["pending_bucket_node_bound"] == "stage.beam_width"
        assert beam_plan["memory_estimate_contract"]["destination_bucket_retention"] == "destination_bucket_accumulator_exact_batch_equivalent"
        assert beam_plan["memory_estimate_contract"]["destination_bucket_accumulator_algorithm"] == "chunked_exact_future_fingerprint_upsert_spill_finalized_by_batch_global_and_diversity_retention"
        assert beam_plan["memory_estimate_contract"]["destination_bucket_no_per_child_full_retained_selection"] is True
        assert beam_plan["memory_estimate_contract"]["destination_bucket_insertion_order_independent"] is True
        assert beam_plan["memory_estimate_contract"]["destination_bucket_partition_merge_independent"] is True
        assert beam_plan["memory_estimate_contract"]["destination_accumulator_unique_fingerprint_bound"] == "stage.destination_accumulator_unique_fingerprint_bound"
        assert beam_plan["memory_estimate_contract"]["destination_accumulator_spill_policy"] == "atomic_compressed_json_gz_chunks_hash_validated_resume_exact"
        assert beam_plan["memory_estimate_contract"]["destination_accumulator_checkpoint_manifest"] == "compact_manifest_with_paths_sha256_counts_and_metrics_no_node_payloads"
        assert beam_plan["memory_estimate_contract"]["compact_cli_output_contract"] == "stdout_summary_only_no_frontier_nodes_route_store_accumulator_payloads_or_timelines"
        assert beam_plan["memory_estimate_contract"]["metric_conservation_contract"] == "candidates_seen_equals_exact_duplicates_plus_unique_fingerprints_and_unique_equals_final_retained_plus_final_rejected"
        assert beam_plan["memory_estimate_contract"]["canonical_route_lineage_tie_contract"] == "lineage_tie_key_before_internal_node_id"
        assert beam_plan["memory_estimate_contract"]["accumulator_index_bytes_per_node"] == 128
        assert beam_plan["memory_estimate_contract"]["limit_check_interval_expansions"] == 64
        assert beam_plan["stages"][0]["destination_accumulator_unique_fingerprint_bound"] == 8192
        assert beam_plan["stages"][1]["destination_accumulator_unique_fingerprint_bound"] == 32768
        assert beam_plan["final_reporting_contract"]["short_horizon_reference_damage_status"] == "horizon_mismatch_not_comparable"
        assert beam_plan["final_reporting_contract"]["short_horizon_numeric_reference_ranking"] is False
        model_bytes = zf.read("models/maskable_ppo_bc_v105.zip")
        assert bytes_sha256(model_bytes) == EXPECTED_BC_MODEL_SHA256
        ppo_model_bytes = zf.read("models/maskable_ppo_candidate_after_bc_v105.zip")
        assert bytes_sha256(ppo_model_bytes) == EXPECTED_PPO_MODEL_SHA256
        guarded_stats = _assert_guarded_completed_archive(zf, name_set)
        _assert_evaluation_summary(evaluation_summary)
        _assert_ppo_evaluation_summary(ppo_summary)
        _assert_comparison(comparison)
        npz_bytes = zf.read("data/generated/manual_120s_bc_demonstration_v105.npz")
        npz_sha = bytes_sha256(npz_bytes)
        assert summary["dataset_sha256"] == npz_sha
        assert _progress_contains(progress, npz_sha)
        with np.load(io.BytesIO(npz_bytes), allow_pickle=False) as data:
            metadata = json.loads(str(np.asarray(data["metadata_json"]).item()))
        assert metadata["source_route_file_sha256"] == SOURCE_ROUTE_FILE_SHA256
        assert summary["metadata"]["source_route_file_sha256"] == SOURCE_ROUTE_FILE_SHA256

        manifest_a = zf.read("direct_action_data_patch_manifest_v61.json")
        manifest_b = zf.read("data/source/direct_action_data_patch_manifest_v61.json")
        assert manifest_a == manifest_b
        assert bytes_sha256(manifest_a) == DIRECT_ACTION_MANIFEST_SHA256

        text_stats = scan_archive_text(zf, names)
        assert text_stats["utf8_bom_count"] == 0
        assert text_stats["replacement_character_count"] == 0
        assert text_stats["forbidden_corrupted_sheet_occurrence_count"] == 0
        assert text_stats["established_mojibake_occurrence_count"] == 0
        assert text_stats["correct_sheet_occurrence_count"] > 0
        assert text_stats["authoritative_correct_sheet_occurrence_count"] > 0

    fresh_extraction_results = run_fresh_extraction_checks(archive)
    if DEFAULT_DEMO_PATH.exists():
        assert file_sha256(DEFAULT_DEMO_PATH) == npz_sha
    return {
        "archive": archive.as_posix(),
        "archive_sha256": file_sha256(archive),
        "zip_entry_count": len(names),
        "cache_entry_count": len(cache_entries),
        "obsolete_bc_eval_bundle_entry_count": len(obsolete_bundle_entries),
        "route_sha256": SOURCE_ROUTE_FILE_SHA256,
        "npz_sha256": npz_sha,
        "bc_model_sha256": EXPECTED_BC_MODEL_SHA256,
        "ppo_model_sha256": EXPECTED_PPO_MODEL_SHA256,
        **guarded_stats,
        "direct_action_manifest_sha256": DIRECT_ACTION_MANIFEST_SHA256,
        **text_stats,
        "fresh_extraction_checks": fresh_extraction_results,
    }


def _assert_guarded_completed_archive(zf: zipfile.ZipFile, name_set: set[str]) -> dict[str, Any]:
    state = json.loads(zf.read("results/guarded_ppo_v109/experiment_state.json").decode("utf-8"))
    final_summary = json.loads(zf.read("results/guarded_ppo_v109/final_experiment_summary.json").decode("utf-8"))
    best = json.loads(zf.read("results/guarded_ppo_v109/best_checkpoint.json").decode("utf-8"))
    leaderboard = json.loads(zf.read("results/guarded_ppo_v109/leaderboard.json").decode("utf-8"))
    assert state["plan_sha256"] == EXPECTED_GUARDED_PLAN_SHA256
    assert final_summary["plan_sha256"] == EXPECTED_GUARDED_PLAN_SHA256
    assert final_summary["candidate"] == "110"
    assert final_summary["latest_verified_baseline"] == "109"
    assert final_summary["no_guarded_checkpoint_exceeded_bc"] is True
    assert final_summary["global_optimum_proven"] is False
    assert final_summary["route_similarity_usage"] == "diagnostic_only_not_used_for_winner_selection"
    provenance = state["completed_experiment_provenance"]
    assert provenance["trained_branch_count"] == 3
    assert provenance["trained_checkpoint_count"] == 30
    assert provenance["failed_chunk_count"] == 0
    assert provenance["requested_aggregate_timesteps"] == 300000
    assert provenance["actual_aggregate_model_timesteps"] == 307200
    assert best["winner_kind"] == "verified_bc_model"
    assert best["model_path"] == "models/maskable_ppo_bc_v105.zip"
    _assert_close(best["total_damage"], EXPECTED_EVAL_TOTAL_DAMAGE)
    assert leaderboard["global_best"]["winner_kind"] == "verified_bc_model"

    guarded_models: list[str] = []
    guarded_sidecars: list[str] = []
    guarded_summaries: list[str] = []
    guarded_timelines: list[str] = []
    for branch_id, branch_state in state["branches"].items():
        records = [item for item in branch_state["chunks"] if item.get("kind") == "guarded_ppo_checkpoint"]
        assert len(records) == 10
        assert [item["chunk_index"] for item in records] == list(range(1, 11))
        expected_seed = 11 if branch_id == "bc_conservative_seed_11" else 73 if branch_id == "bc_exploratory_seed_73" else 137
        assert [item["actual_model_seed"] for item in records] == list(range(expected_seed, expected_seed + 10))
        for record in records:
            model_path = record["checkpoint_path"]
            sidecar_path = record["metadata_path"]
            summary_path = record["summary_path"]
            timeline_path = record["timeline_path"]
            for required in (model_path, sidecar_path, summary_path, timeline_path):
                assert required in name_set, required
            assert bytes_sha256(zf.read(model_path)) == record["checkpoint_sha256"]
            assert bytes_sha256(zf.read(sidecar_path)) == record["metadata_sha256"]
            assert bytes_sha256(zf.read(summary_path)) == record["summary_sha256"]
            assert bytes_sha256(zf.read(timeline_path)) == record["timeline_sha256"]
            with zipfile.ZipFile(io.BytesIO(zf.read(model_path))) as model_zip:
                model_data = json.loads(model_zip.read("data").decode("utf-8"))
            assert int(model_data["seed"]) == int(record["actual_model_seed"])
            assert int(model_data["num_timesteps"]) == int(record["actual_model_num_timesteps"])
            assert int(model_data["n_steps"]) == 512
            sidecar = json.loads(zf.read(sidecar_path).decode("utf-8"))
            assert sidecar["model_path"] == model_path
            assert sidecar["model_sha256"] == record["checkpoint_sha256"]
            assert sidecar["actual_model_seed"] == record["actual_model_seed"]
            assert sidecar["actual_model_num_timesteps"] == record["actual_model_num_timesteps"]
            guarded_models.append(model_path)
            guarded_sidecars.append(sidecar_path)
            guarded_summaries.append(summary_path)
            guarded_timelines.append(timeline_path)

    zip_entries = {name for name in name_set if name.endswith(".zip")}
    expected_zip_entries = {
        "models/maskable_ppo_bc_v105.zip",
        "models/maskable_ppo_candidate_after_bc_v105.zip",
        *guarded_models,
    }
    assert zip_entries == expected_zip_entries
    assert len(guarded_models) == 30
    assert len(guarded_sidecars) == 30
    assert len(guarded_summaries) == 30
    assert len(guarded_timelines) == 30
    return {
        "guarded_model_zip_count": len(guarded_models),
        "guarded_sidecar_count": len(guarded_sidecars),
        "guarded_summary_count": len(guarded_summaries),
        "guarded_timeline_count": len(guarded_timelines),
        "guarded_requested_aggregate_timesteps": provenance["requested_aggregate_timesteps"],
        "guarded_actual_aggregate_model_timesteps": provenance["actual_aggregate_model_timesteps"],
    }


def scan_archive_text(zf: zipfile.ZipFile, names: list[str]) -> dict[str, int]:
    stats = {
        "text_entry_count": 0,
        "utf8_bom_count": 0,
        "replacement_character_count": 0,
        "forbidden_corrupted_sheet_occurrence_count": 0,
        "established_mojibake_occurrence_count": 0,
        "correct_sheet_occurrence_count": 0,
        "authoritative_correct_sheet_occurrence_count": 0,
    }
    for name in names:
        if not name.endswith(TEXT_SUFFIXES):
            continue
        data = zf.read(name)
        stats["text_entry_count"] += 1
        if data.startswith(b"\xef\xbb\xbf"):
            stats["utf8_bom_count"] += 1
        text = data.decode("utf-8")
        stats["replacement_character_count"] += text.count("\uFFFD")
        stats["forbidden_corrupted_sheet_occurrence_count"] += text.count(FORBIDDEN_CORRUPTED_SHEET_NAME)
        stats["correct_sheet_occurrence_count"] += text.count(CORRECT_SHEET_NAME)
        if name in AUTHORITATIVE_SOURCE_FILES:
            stats["authoritative_correct_sheet_occurrence_count"] += text.count(CORRECT_SHEET_NAME)
        for marker in ESTABLISHED_MOJIBAKE_MARKERS:
            stats["established_mojibake_occurrence_count"] += text.count(marker)
        if name.endswith(".json"):
            _assert_json(data)
    return stats


def run_fresh_extraction_checks(archive: Path) -> list[dict[str, Any]]:
    checks = [
        [sys.executable, "scripts/project_progress_active_echo_alignment_smoke_test.py"],
        [sys.executable, "scripts/project_progress_manual_120s_baseline_alignment_smoke_test.py"],
        [sys.executable, "scripts/project_progress_bc_demo_alignment_smoke_test.py"],
        [sys.executable, "scripts/project_progress_ppo_100k_alignment_smoke_test.py"],
        [sys.executable, "scripts/project_progress_guarded_ppo_alignment_smoke_test.py"],
        [sys.executable, "scripts/project_progress_guarded_ppo_results_alignment_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_completed_experiment_integrity_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_route_similarity_diagnostic_only_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_plan_contract_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_branch_continuation_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_damage_only_objective_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_scratch_control_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_cli_execution_gate_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_seed_contract_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_incumbent_best_retention_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_state_integrity_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_route_diagnostics_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_stage_timeout_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_cross_platform_path_canonicalization_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_checkpoint_sidecar_strict_contract_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_completed_experiment_spot_evaluation_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_dry_run_step0_alias_smoke_test.py"],
        [sys.executable, "scripts/guarded_ppo_short_integration_smoke_test.py"],
        [sys.executable, "scripts/manual_120s_bc_demo_contract_smoke_test.py"],
        [sys.executable, "scripts/manual_120s_bc_packaged_generation_parity_smoke_test.py"],
        [sys.executable, "scripts/manual_120s_bc_report_portability_smoke_test.py"],
        [sys.executable, "scripts/bc_pretrain_evaluator_contract_smoke_test.py"],
        [sys.executable, "scripts/evaluation_event_source_damage_attribution_smoke_test.py"],
        [sys.executable, "scripts/evaluation_scheduled_damage_role_breakdown_smoke_test.py"],
        [sys.executable, "scripts/bc_evaluation_manual_baseline_parity_smoke_test.py"],
        [sys.executable, "scripts/ppo_100k_evaluation_contract_smoke_test.py"],
        [sys.executable, "scripts/manual_bc_ppo_comparison_smoke_test.py"],
        [sys.executable, "scripts/build_candidate_archive_output_guard_smoke_test.py"],
        [sys.executable, "scripts/project_progress_beam_search_alignment_smoke_test.py"],
        [sys.executable, "scripts/beam_search_plan_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_clone_isolation_smoke_test.py"],
        [sys.executable, "scripts/beam_search_clone_behavioral_parity_smoke_test.py"],
        [sys.executable, "scripts/beam_search_state_roundtrip_smoke_test.py"],
        [sys.executable, "scripts/beam_search_state_fingerprint_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_state_payload_size_smoke_test.py"],
        [sys.executable, "scripts/beam_search_exact_dedup_dominance_smoke_test.py"],
        [sys.executable, "scripts/beam_search_true_time_bucket_smoke_test.py"],
        [sys.executable, "scripts/beam_search_legal_action_expansion_smoke_test.py"],
        [sys.executable, "scripts/beam_search_zero_time_action_smoke_test.py"],
        [sys.executable, "scripts/beam_search_cutoff_scheduler_smoke_test.py"],
        [sys.executable, "scripts/beam_search_delayed_payoff_diversity_smoke_test.py"],
        [sys.executable, "scripts/beam_search_real_diversity_key_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_damage_only_winner_smoke_test.py"],
        [sys.executable, "scripts/beam_search_manual_route_independence_guard_smoke_test.py"],
        [sys.executable, "scripts/beam_search_resume_integrity_smoke_test.py"],
        [sys.executable, "scripts/beam_search_resume_equivalence_smoke_test.py"],
        [sys.executable, "scripts/beam_search_realistic_2000_resume_equivalence_smoke_test.py"],
        [sys.executable, "scripts/beam_search_hot_path_scalability_smoke_test.py"],
        [sys.executable, "scripts/beam_search_checkpoint_interval_smoke_test.py"],
        [sys.executable, "scripts/beam_search_route_store_compaction_smoke_test.py"],
        [sys.executable, "scripts/beam_search_diversity_phase_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_future_field_classification_smoke_test.py"],
        [sys.executable, "scripts/beam_search_short_window_diversity_smoke_test.py"],
        [sys.executable, "scripts/beam_search_horizon_comparison_guard_smoke_test.py"],
        [sys.executable, "scripts/beam_search_pending_frontier_bound_smoke_test.py"],
        [sys.executable, "scripts/beam_search_peak_live_metric_smoke_test.py"],
        [sys.executable, "scripts/beam_search_intra_bucket_budget_guard_smoke_test.py"],
        [sys.executable, "scripts/beam_search_partial_node_resume_smoke_test.py"],
        [sys.executable, "scripts/beam_search_final_replay_reporting_smoke_test.py"],
        [sys.executable, "scripts/beam_search_terminal_replay_parity_smoke_test.py"],
        [sys.executable, "scripts/beam_search_completed_route_reporting_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_completion_order_smoke_test.py"],
        [sys.executable, "scripts/beam_search_memory_bound_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_destination_accumulator_hot_path_smoke_test.py"],
        [sys.executable, "scripts/beam_search_destination_accumulator_spill_smoke_test.py"],
        [sys.executable, "scripts/beam_search_destination_accumulator_manifest_size_smoke_test.py"],
        [sys.executable, "scripts/beam_search_compact_cli_output_smoke_test.py"],
        [sys.executable, "scripts/beam_search_accumulator_metrics_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_duplicate_lineage_tie_smoke_test.py"],
        [sys.executable, "scripts/beam_search_destination_bucket_order_independence_smoke_test.py"],
        [sys.executable, "scripts/beam_search_destination_bucket_batch_equivalence_smoke_test.py"],
        [sys.executable, "scripts/beam_search_destination_bucket_partition_merge_smoke_test.py"],
        [sys.executable, "scripts/beam_search_destination_bucket_resume_equivalence_smoke_test.py"],
        [sys.executable, "scripts/beam_search_diversity_quota_fill_smoke_test.py"],
        [sys.executable, "scripts/beam_search_cli_execution_gate_smoke_test.py"],
        [sys.executable, "scripts/beam_search_bounded_integration_smoke_test.py"],
        [
            sys.executable,
            "rl/pretrain_maskable_ppo_bc.py",
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--initial-active-character",
            "aemeath",
            "--demo-path",
            "data/generated/manual_120s_bc_demonstration_v105.npz",
            "--model-path",
            "models/maskable_ppo_bc_v105.zip",
            "--dry-run",
        ],
        [
            sys.executable,
            "rl/evaluate_maskable_ppo.py",
            "--model-path",
            "models/maskable_ppo_candidate_after_bc_v105.zip",
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--initial-active-character",
            "aemeath",
            "--summary-path",
            "results/ppo_100k_evaluation_summary.json",
            "--timeline-path",
            "results/ppo_100k_timeline.csv",
        ],
        [
            sys.executable,
            "rl/evaluate_maskable_ppo.py",
            "--model-path",
            "models/maskable_ppo_bc_v105.zip",
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--initial-active-character",
            "aemeath",
        ],
    ]
    passed: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        extract_root = Path(temp_dir) / "project"
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract_root)
        for command in checks:
            result = _run(command, cwd=extract_root, timeout=240)
            passed.append(
                {
                    "command": " ".join(command[1:]),
                    "elapsed_seconds": round(result["elapsed_seconds"], 6),
                }
            )
    return passed


def _assert_json(data: bytes) -> None:
    json.loads(data.decode("utf-8"))


def _assert_evaluation_summary(summary: dict[str, Any]) -> None:
    assert summary["selected_action_count"] == 148
    assert summary["resolved_action_count"] == 148
    assert summary["selected_sequence_sha256"] == EXPECTED_EVAL_SELECTED_SEQUENCE_SHA256
    assert summary["resolved_sequence_sha256"] == EXPECTED_EVAL_RESOLVED_SEQUENCE_SHA256
    assert summary["manual_baseline_selected_sequence_match"] is True
    assert summary["manual_baseline_resolved_sequence_match"] is True
    assert summary["manual_baseline_character_damage_match"] is True
    assert summary["model_metadata_mismatches"] == {}
    assert summary["model_space_mismatches"] == {}
    _assert_close(summary["total_damage"], EXPECTED_EVAL_TOTAL_DAMAGE)
    _assert_close(summary["dps"], EXPECTED_EVAL_DPS)
    for character_id, expected_damage in EXPECTED_DAMAGE_BY_CHARACTER.items():
        _assert_close(summary["damage_by_character"][character_id], expected_damage)
    role_breakdown = summary["effective_damage_role_breakdown"]
    _assert_close(role_breakdown["scheduled_damage"], EXPECTED_SCHEDULED_DAMAGE)
    _assert_close(role_breakdown["total_damage_delta"], 0.0)


def _assert_ppo_evaluation_summary(summary: dict[str, Any]) -> None:
    assert summary["selected_action_count"] == 152
    assert summary["resolved_action_count"] == 152
    assert summary["selected_sequence_sha256"] == EXPECTED_PPO_SELECTED_SEQUENCE_SHA256
    assert summary["resolved_sequence_sha256"] == EXPECTED_PPO_RESOLVED_SEQUENCE_SHA256
    assert summary["manual_baseline_selected_sequence_match"] is False
    assert summary["manual_baseline_resolved_sequence_match"] is False
    assert summary["manual_baseline_character_damage_match"] is False
    assert summary["model_metadata_mismatches"] == {}
    assert summary["model_space_mismatches"] == {}
    assert summary["model_training_metadata_source"] == "ppo_model_sidecar"
    assert summary["model_training_metadata_path"] == "models/maskable_ppo_candidate_after_bc_v105.zip.ppo_metadata.json"
    _assert_close(summary["total_damage"], EXPECTED_PPO_TOTAL_DAMAGE)
    _assert_close(summary["dps"], EXPECTED_PPO_DPS)
    _assert_close(summary["final_time"], 120.0)
    _assert_close(summary["manual_baseline_total_damage"], 5165134.682363359)
    _assert_close(summary["manual_baseline_damage_ratio"], 0.6971042094839032)
    _assert_close(summary["manual_baseline_damage_delta"], -1564497.5527365585)
    for character_id, expected_damage in EXPECTED_PPO_DAMAGE_BY_CHARACTER.items():
        _assert_close(summary["damage_by_character"][character_id], expected_damage)
    role_breakdown = summary["effective_damage_role_breakdown"]
    _assert_close(role_breakdown["scheduled_damage"], EXPECTED_PPO_SCHEDULED_DAMAGE)
    _assert_close(role_breakdown["total_damage_delta"], 0.0)


def _assert_comparison(comparison: dict[str, Any]) -> None:
    assert comparison["schema_version"] == "manual_bc_ppo_comparison_v108"
    assert comparison["objective"] == "final_120_second_total_damage_only"
    assert comparison["winner"] == "bc_model"
    assert comparison["winner_model"] == "models/maskable_ppo_bc_v105.zip"
    assert comparison["ppo_candidate_classification"] == "valid_but_regressed"
    assert comparison["models"]["bc_model"]["sha256"] == EXPECTED_BC_MODEL_SHA256
    assert comparison["models"]["ppo_100k_candidate"]["sha256"] == EXPECTED_PPO_MODEL_SHA256
    results = comparison["results"]
    _assert_close(results["bc_model"]["total_damage"], EXPECTED_EVAL_TOTAL_DAMAGE)
    _assert_close(results["ppo_100k"]["total_damage"], EXPECTED_PPO_TOTAL_DAMAGE)
    assert results["ppo_100k"]["first_selected_action_divergence"] == {
        "zero_based_step": 4,
        "baseline": "aemeath_resonance_skill",
        "ppo": "swap_to_mornye",
    }


def _assert_close(actual: float, expected: float, *, tolerance: float = 1e-6) -> None:
    assert abs(float(actual) - expected) <= tolerance, (actual, expected)


def _is_cache_entry(name: str) -> bool:
    normalized = name.replace("\\", "/")
    parts = normalized.split("/")
    return (
        "__pycache__" in parts
        or ".pytest_cache" in parts
        or normalized.endswith((".pyc", ".pyo"))
    )


def _progress_contains(progress: object, value: str) -> bool:
    if isinstance(progress, dict):
        return any(_progress_contains(item, value) for item in progress.values())
    if isinstance(progress, list):
        return any(_progress_contains(item, value) for item in progress)
    return progress == value


def _run(command: list[str], *, cwd: Path, timeout: float) -> dict[str, Any]:
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    label = " ".join(command[1:])
    print(f"fresh-extraction check start: {label}", flush=True)
    started = time.perf_counter()
    stdout_fd, stdout_name = tempfile.mkstemp(prefix="archive-check-stdout-", suffix=".txt")
    stderr_fd, stderr_name = tempfile.mkstemp(prefix="archive-check-stderr-", suffix=".txt")
    os.close(stdout_fd)
    os.close(stderr_fd)
    stdout_path = Path(stdout_name)
    stderr_path = Path(stderr_name)
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process_kwargs: dict[str, Any] = {
        "cwd": cwd,
        "env": env,
        "stdout": None,
        "stderr": None,
        "creationflags": creationflags,
        "text": False,
    }
    if os.name != "nt":
        process_kwargs["start_new_session"] = True
    try:
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process_kwargs["stdout"] = stdout_file
            process_kwargs["stderr"] = stderr_file
            process = subprocess.Popen(command, **process_kwargs)
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                _terminate_process_tree(process)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    _kill_process_tree(process)
                    process.wait(timeout=10)
                elapsed = time.perf_counter() - started
                stdout_file.flush()
                stderr_file.flush()
                raise AssertionError(
                    _format_process_failure(
                        command=command,
                        timeout=timeout,
                        elapsed=elapsed,
                        stdout=_read_text(stdout_path),
                        stderr=_read_text(stderr_path),
                    )
                ) from exc
            elapsed = time.perf_counter() - started
            stdout_file.flush()
            stderr_file.flush()
        stdout = _read_text(stdout_path)
        stderr = _read_text(stderr_path)
        if returncode != 0:
            raise AssertionError(
                _format_process_failure(
                    command=command,
                    timeout=timeout,
                    elapsed=elapsed,
                    stdout=stdout,
                    stderr=stderr,
                    returncode=returncode,
                )
            )
        print(f"fresh-extraction check ok: {label} ({elapsed:.3f}s)", flush=True)
        return {"elapsed_seconds": elapsed, "stdout": stdout, "stderr": stderr}
    finally:
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def _kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def _format_process_failure(
    *,
    command: list[str],
    timeout: float,
    elapsed: float,
    stdout: str,
    stderr: str,
    returncode: int | None = None,
) -> str:
    status = f"returncode={returncode}" if returncode is not None else "timeout"
    return (
        f"Fresh extraction check failed ({status})\n"
        f"command: {' '.join(command)}\n"
        f"timeout_seconds: {timeout}\n"
        f"elapsed_seconds: {elapsed:.6f}\n"
        f"stdout:\n{stdout}\n"
        f"stderr:\n{stderr}"
    )


if __name__ == "__main__":
    main()
