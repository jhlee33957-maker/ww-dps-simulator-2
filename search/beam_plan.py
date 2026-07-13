from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from rl.demo_contract import action_data_hash, party_config_hash
from search.beam_state import diversity_quantization_contract


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = ROOT / "data" / "beam_search_plan_v111.json"
EXPECTED_ALGORITHM = "deterministic_diverse_time_bucket_beam_search"
EXPECTED_OBJECTIVE = "deterministic_120s_total_damage_only"
EXPECTED_PARTY = "aemeath_mornye_lynae_enabled_test_party"
EXPECTED_INITIAL_ACTIVE = "aemeath"
EXPECTED_CURRICULUM = "none"
EXPECTED_ACTION_DATA_HASH = "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1"
EXPECTED_PARTY_CONFIG_HASH = "bd106ba1c0f5581436c35fea736a00fd6ad92b131f8b43ba8cf1e3dc89cbcb11"
EXPECTED_DIRECT_ACTION_MANIFEST_SHA256 = "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d"
EXPECTED_BC_NPZ_SHA256 = "b020a1b9309b46bd87eb3fff4837aead53035c4c84620962f47feb9fc11846ff"
EXPECTED_BC_MODEL_SHA256 = "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e"
EXPECTED_PPO_MODEL_SHA256 = "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513"
EXPECTED_GUARDED_PLAN_SHA256 = "0306c734347e49460fd7273bce546eed80a2db657e460eb707f5cab961a9e0e6"
EXPECTED_ROUTE_SHA256 = "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a"
HASH_FILE_PATHS = {
    "direct_action_manifest_sha256": ROOT / "direct_action_data_patch_manifest_v61.json",
    "direct_action_manifest_copy_sha256": ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json",
    "bc_npz_sha256": ROOT / "data" / "generated" / "manual_120s_bc_demonstration_v105.npz",
    "bc_model_sha256": ROOT / "models" / "maskable_ppo_bc_v105.zip",
    "prior_ppo_model_sha256": ROOT / "models" / "maskable_ppo_candidate_after_bc_v105.zip",
    "guarded_ppo_plan_sha256": ROOT / "data" / "guarded_ppo_experiment_plan_v109.json",
    "manual_route_raw_sha256": ROOT / "data" / "manual_120s_baseline_routes_v104.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_plan(path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_plan(plan: dict[str, Any], *, plan_path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "schema_version": "beam_search_plan_v111",
        "algorithm": EXPECTED_ALGORITHM,
        "objective": EXPECTED_OBJECTIVE,
        "party": EXPECTED_PARTY,
        "initial_active_character": EXPECTED_INITIAL_ACTIVE,
        "curriculum_reset_mode": EXPECTED_CURRICULUM,
        "route_similarity_objective": False,
        "bc_ppo_policy_guidance": False,
        "manual_route_guidance": False,
        "global_optimum_proven": False,
    }
    for key, expected in checks.items():
        if plan.get(key) != expected:
            errors.append(f"{key} {plan.get(key)!r} != {expected!r}")
    if float(plan.get("combat_duration", 0.0)) != 120.0:
        errors.append("combat_duration must be 120.0")
    observation = plan.get("observation_contract", {})
    for key, expected in {
        "version": "slot_generic_mechanics_v5",
        "shape": 314,
        "policy_action_count": 25,
        "max_policy_action_slots": 32,
    }.items():
        if observation.get(key) != expected:
            errors.append(f"observation_contract.{key} {observation.get(key)!r} != {expected!r}")
    for key in ("character_specific_reward", "swap_reward", "buff_use_reward", "manual_prefix_preservation"):
        if plan.get(key) is not False:
            errors.append(f"{key} must be false")
    if int(plan.get("checkpoint_interval_expansions", 0)) != 100000:
        errors.append("checkpoint_interval_expansions must be 100000")
    if int(plan.get("completed_route_leaderboard_size", 0)) != 128:
        errors.append("completed_route_leaderboard_size must be 128")
    if plan.get("state_payload_contract", {}).get("objective_reporting_fields_omitted_except_total_damage") is not True:
        errors.append("state_payload_contract must omit objective/reporting fields except total_damage")
    checkpoint = plan.get("checkpoint_contract", {})
    if checkpoint.get("dirty_bucket_only_between_forced_writes") is not True:
        errors.append("checkpoint_contract.dirty_bucket_only_between_forced_writes must be true")
    resume = plan.get("resume_contract", {})
    for key in (
        "atomic_frontier_writes",
        "pending_bucket_manifest",
        "completed_bucket_manifest",
        "completed_routes_preserved",
        "partial_node_action_cursor",
        "dirty_bucket_checkpoint_writes",
        "plan_hash_validated",
        "stage_hash_validated",
        "actual_data_hashes_validated",
    ):
        if resume.get(key) is not True:
            errors.append(f"resume_contract.{key} must be true")
    route_store = plan.get("route_store_contract", {})
    if route_store.get("completed_route_records") != "compact_bounded_leaderboard":
        errors.append("route_store_contract.completed_route_records must be compact_bounded_leaderboard")
    memory = plan.get("memory_estimate_contract", {})
    for key in ("concurrent_bucket_count", "route_store_bytes_per_edge", "scratch_bytes_per_node", "safety_factor", "pending_bucket_node_bound", "live_node_budget_formula", "destination_bucket_retention", "destination_bucket_accumulator_algorithm", "destination_bucket_no_per_child_full_retained_selection", "destination_accumulator_unique_fingerprint_bound", "destination_accumulator_checkpoint_manifest", "compact_cli_output_contract", "metric_conservation_contract", "canonical_route_lineage_tie_contract", "accumulator_index_bytes_per_node", "limit_check_interval_expansions"):
        if key not in memory:
            errors.append(f"memory_estimate_contract missing {key}")
    reporting = plan.get("final_reporting_contract", {})
    if reporting.get("bc_incumbent_manifest_complete") is not True:
        errors.append("final_reporting_contract.bc_incumbent_manifest_complete must be true")
    for key, expected in {
        "short_horizon_reference_damage_status": "horizon_mismatch_not_comparable",
        "reference_damage_comparison_horizon_seconds": 120.0,
        "short_horizon_numeric_reference_ranking": False,
    }.items():
        if reporting.get(key) != expected:
            errors.append(f"final_reporting_contract.{key} {reporting.get(key)!r} != {expected!r}")
    stages = plan.get("stages")
    if not isinstance(stages, list) or [stage.get("stage_id") for stage in stages] != ["calibration_30s", "full_120s"]:
        errors.append("plan must contain exactly calibration_30s and full_120s stages")
    else:
        expected = {
            "calibration_30s": {
                "combat_duration": 30.0,
                "time_bucket_width": 0.5,
                "beam_width": 1024,
                "global_damage_quota": 512,
                "diversity_retention_quota": 512,
                "max_states_per_diversity_key": 8,
                "maximum_expansions": 500000,
                "wall_clock_limit_seconds": 1800.0,
                "memory_budget_bytes": 10905714688,
                "limit_check_interval_expansions": 64,
                "destination_accumulator_unique_fingerprint_bound": 8192,
            },
            "full_120s": {
                "combat_duration": 120.0,
                "time_bucket_width": 0.5,
                "beam_width": 4096,
                "global_damage_quota": 2048,
                "diversity_retention_quota": 2048,
                "max_states_per_diversity_key": 8,
                "maximum_expansions": 5000000,
                "wall_clock_limit_seconds": 14400.0,
                "memory_budget_bytes": 43619713024,
                "limit_check_interval_expansions": 64,
                "destination_accumulator_unique_fingerprint_bound": 32768,
            },
        }
        for stage in stages:
            expected_stage = expected[stage["stage_id"]]
            for key, value in expected_stage.items():
                if stage.get(key) != value:
                    errors.append(f"{stage['stage_id']}.{key} {stage.get(key)!r} != {value!r}")
            if stage.get("global_damage_quota", 0) + stage.get("diversity_retention_quota", 0) != stage.get("beam_width"):
                errors.append(f"{stage['stage_id']} quotas must sum to beam_width")
            if stage.get("maximum_expansions", 0) <= 0:
                errors.append(f"{stage['stage_id']} maximum_expansions must be positive")
    hashes = plan.get("data_contract_hashes", {})
    hash_checks = {
        "action_data_hash": EXPECTED_ACTION_DATA_HASH,
        "party_config_hash": EXPECTED_PARTY_CONFIG_HASH,
        "direct_action_manifest_sha256": EXPECTED_DIRECT_ACTION_MANIFEST_SHA256,
        "bc_npz_sha256": EXPECTED_BC_NPZ_SHA256,
        "bc_model_sha256": EXPECTED_BC_MODEL_SHA256,
        "prior_ppo_model_sha256": EXPECTED_PPO_MODEL_SHA256,
        "guarded_ppo_plan_sha256": EXPECTED_GUARDED_PLAN_SHA256,
        "manual_route_raw_sha256": EXPECTED_ROUTE_SHA256,
    }
    for key, expected in hash_checks.items():
        if hashes.get(key) != expected:
            errors.append(f"{key} {hashes.get(key)!r} != {expected!r}")
    actual_hashes = resolve_actual_data_hashes()
    for key, expected in hash_checks.items():
        actual = actual_hashes.get(key)
        if actual != expected:
            errors.append(f"actual {key} {actual!r} != {expected!r}")
    if actual_hashes["direct_action_manifest_sha256"] != actual_hashes["direct_action_manifest_copy_sha256"]:
        errors.append("direct action manifest copies differ")
    diversity = plan.get("diversity_key_schema", {})
    expected_diversity_values = {
        "combat_time_bucket_seconds": 5.0,
        "resonance_energy_band_points": 25.0,
        "concerto_energy_band_points": 25.0,
        "enemy_off_tune_ratio_band": 0.25,
        "rupturous_trail_stack_band": 10.0,
        "mechanic_remaining_seconds_band": 5.0,
        "mechanic_stack_band": 5.0,
        "cooldown_ready_boundary_seconds": 0.0,
        "scheduled_effect_phase_band_seconds": 0.5,
        "scheduled_effect_remaining_band_seconds": 1.0,
        "active_buff_remaining_band_seconds": 1.0,
        "short_window_remaining_band_seconds": 0.5,
        "standard_window_remaining_band_seconds": 1.0,
        "long_field_remaining_band_seconds": 5.0,
        "scheduled_effect_signature_cap": 8,
        "buff_signature_cap": 12,
        "route_blind": True,
    }
    for key, expected in expected_diversity_values.items():
        if diversity.get(key) != expected:
            errors.append(f"diversity_key_schema.{key} {diversity.get(key)!r} != {expected!r}")
        if key in plan.get("diversity_quantization", {}) and plan["diversity_quantization"].get(key) != expected:
            errors.append(f"diversity_quantization.{key} {plan['diversity_quantization'].get(key)!r} != {expected!r}")
    required_diversity_sections = {
        "combat_time_bucket_seconds",
        "resonance_energy_band_points",
        "concerto_energy_band_points",
        "enemy_off_tune_ratio_band",
        "rupturous_trail_stack_band",
        "mechanic_remaining_seconds_band",
        "mechanic_stack_band",
        "scheduled_effect_phase_band_seconds",
        "declared_character_mechanic_fields",
        "declared_mechanic_field_encoders",
    }
    missing_diversity = sorted(required_diversity_sections - set(diversity))
    if missing_diversity:
        errors.append(f"diversity_key_schema missing {missing_diversity}")
    if plan.get("deduplication", {}).get("future_state_fingerprint") != "exact_combat_state_future_affecting_fields":
        errors.append("deduplication.future_state_fingerprint contract changed")
    if plan.get("deduplication", {}).get("total_damage_in_fingerprint") is not False:
        errors.append("total_damage must not be part of future fingerprint")
    expected_diversity_contract = diversity_quantization_contract()
    if diversity.get("declared_character_mechanic_fields") != expected_diversity_contract["declared_character_mechanic_fields"]:
        errors.append("diversity_key_schema.declared_character_mechanic_fields does not match runtime contract")
    if diversity.get("declared_mechanic_field_encoders") != expected_diversity_contract["declared_mechanic_field_encoders"]:
        errors.append("diversity_key_schema.declared_mechanic_field_encoders does not match runtime contract")
    required_concurrent = _derived_concurrent_bucket_count(float(stages[0]["time_bucket_width"]) if isinstance(stages, list) and stages else 0.5)
    if int(memory.get("concurrent_bucket_count", 0)) < required_concurrent["required_concurrent_bucket_count"]:
        errors.append(
            "memory_estimate_contract.concurrent_bucket_count "
            f"{memory.get('concurrent_bucket_count')!r} below derived {required_concurrent['required_concurrent_bucket_count']}"
        )
    for key, expected in {
        "current_bucket_allowance": 1,
        "bucket_safety_margin": 2,
        "max_resolved_combat_time_cost": required_concurrent["max_resolved_combat_time_cost"],
        "max_resolved_combat_time_cost_action_id": required_concurrent["max_resolved_combat_time_cost_action_id"],
        "pending_bucket_node_bound": "stage.beam_width",
        "live_node_budget_formula": "stage.beam_width * concurrent_bucket_count",
        "destination_bucket_retention": "destination_bucket_accumulator_exact_batch_equivalent",
        "destination_bucket_accumulator_algorithm": "chunked_exact_future_fingerprint_upsert_spill_finalized_by_batch_global_and_diversity_retention",
        "destination_bucket_no_per_child_full_retained_selection": True,
        "destination_bucket_insertion_order_independent": True,
        "destination_bucket_partition_merge_independent": True,
        "destination_accumulator_unique_fingerprint_bound": "stage.destination_accumulator_unique_fingerprint_bound",
        "destination_accumulator_spill_policy": "atomic_compressed_json_gz_chunks_hash_validated_resume_exact",
        "destination_accumulator_checkpoint_manifest": "compact_manifest_with_paths_sha256_counts_and_metrics_no_node_payloads",
        "destination_accumulator_retained_set_finalization_triggers": [
            "earliest_bucket_processing",
            "forced_checkpoint",
            "final_reporting",
        ],
        "compact_cli_output_contract": "stdout_summary_only_no_frontier_nodes_route_store_accumulator_payloads_or_timelines",
        "metric_conservation_contract": "candidates_seen_equals_exact_duplicates_plus_unique_fingerprints_and_unique_equals_final_retained_plus_final_rejected",
        "canonical_route_lineage_tie_contract": "lineage_tie_key_before_internal_node_id",
        "accumulator_index_bytes_per_node": 128,
        "limit_check_interval_expansions": 64,
    }.items():
        if memory.get(key) != expected:
            errors.append(f"memory_estimate_contract.{key} {memory.get(key)!r} != {expected!r}")
    boundary = plan.get("execution_boundary", {})
    if boundary.get("candidate_111_runs_calibration") is not False:
        errors.append("candidate_111_runs_calibration must be false")
    if boundary.get("candidate_111_runs_full_search") is not False:
        errors.append("candidate_111_runs_full_search must be false")
    if boundary.get("candidate_111_runs_mcts") is not False:
        errors.append("candidate_111_runs_mcts must be false")
    if float(boundary.get("smoke_max_combat_duration", 0.0)) > 3.0:
        errors.append("smoke_max_combat_duration must be <= 3.0")
    if int(boundary.get("smoke_max_expansions", 0)) > 2000:
        errors.append("smoke_max_expansions must be <= 2000")
    if "manual_action_sequence" in json.dumps(plan, sort_keys=True).lower():
        errors.append("plan must not embed manual action sequence")
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "ok",
        "plan_path": project_relative(plan_path),
        "plan_sha256": sha256_file(plan_path),
        "stage_ids": [stage["stage_id"] for stage in stages],
        "future_execution_only": True,
        "actual_data_hashes": {key: actual_hashes[key] for key in sorted(hash_checks)},
    }


def stage_by_id(plan: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in plan["stages"]:
        if stage["stage_id"] == stage_id:
            return stage
    raise ValueError(f"Unknown Beam Search stage: {stage_id}")


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def resolve_actual_data_hashes() -> dict[str, str]:
    actual = {
        "action_data_hash": action_data_hash(root=ROOT),
        "party_config_hash": party_config_hash(root=ROOT),
    }
    for key, path in HASH_FILE_PATHS.items():
        actual[key] = sha256_file(path)
    return actual


def _derived_concurrent_bucket_count(time_bucket_width: float) -> dict[str, Any]:
    max_cost, action_id = _max_resolved_combat_time_cost()
    future_offsets = int(math.ceil(max_cost / float(time_bucket_width)))
    return {
        "max_resolved_combat_time_cost": max_cost,
        "max_resolved_combat_time_cost_action_id": action_id,
        "required_concurrent_bucket_count": future_offsets + 1 + 2,
    }


def _max_resolved_combat_time_cost() -> tuple[float, str]:
    candidates: list[tuple[float, str]] = []
    for rel in ("data/actions.json", "data/transition_actions.json"):
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        items = data.values() if isinstance(data, dict) else data
        for item in items:
            if isinstance(item, dict):
                value = item.get("combat_time_cost", item.get("action_time"))
                if isinstance(value, (int, float)):
                    candidates.append((float(value), str(item.get("id") or item.get("action_id") or "unknown")))
    if not candidates:
        raise ValueError("No action combat-time costs found")
    return max(candidates, key=lambda item: item[0])
