from __future__ import annotations

import hashlib
import json
import math
import copy
from pathlib import Path
from typing import Any

from rl.demo_contract import action_data_hash, party_config_hash
from search.beam_state import diversity_quantization_contract


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = ROOT / "data" / "beam_search_plan_v111.json"
LOWMEM_32GB_PLAN_PATH = ROOT / "data" / "beam_search_plan_v113_32gb.json"
V114_LOWMEM_32GB_PLAN_PATH = ROOT / "data" / "beam_search_plan_v114_32gb.json"
V115_RESUME_V114_PLAN_PATH = ROOT / "data" / "beam_search_plan_v115_32gb_resume_v114.json"
LOWMEM_32GB_SCHEMA = "beam_search_plan_v113_32gb"
V114_LOWMEM_32GB_SCHEMA = "beam_search_plan_v114_32gb"
V115_RESUME_V114_SCHEMA = "beam_search_plan_v115_32gb_resume_v114"
LOWMEM_32GB_STAGE_ID = "full_120s_lowmem_32gb"
LOWMEM_32GB_OUTPUT_ROOT = "results/beam_search_v113_lowmem_32gb"
FORBIDDEN_64GB_OUTPUT_ROOT = "results/beam_search_v111_full_120s"
EXPECTED_ALGORITHM = "deterministic_diverse_time_bucket_beam_search"
EXPECTED_OBJECTIVE = "deterministic_120s_total_damage_only"
EXPECTED_PARTY = "aemeath_mornye_lynae_enabled_test_party"
EXPECTED_INITIAL_ACTIVE = "aemeath"
EXPECTED_CURRICULUM = "none"
STREAMING_ACCUMULATOR_SPILL_FORMAT = "streaming_jsonl_gzip_v113"
LEGACY_ACCUMULATOR_SPILL_FORMAT = "legacy_monolithic_json_gzip_v111"
ACCUMULATOR_SPILL_FORMATS = {
    STREAMING_ACCUMULATOR_SPILL_FORMAT,
    LEGACY_ACCUMULATOR_SPILL_FORMAT,
}
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
    raw = json.loads(path.read_text(encoding="utf-8"))
    inheritance = raw.get("inherits_contracts_from")
    if raw.get("schema_version") in {LOWMEM_32GB_SCHEMA, V114_LOWMEM_32GB_SCHEMA, V115_RESUME_V114_SCHEMA} and isinstance(inheritance, dict):
        base_path = ROOT / str(inheritance["path"])
        if sha256_file(base_path) != inheritance.get("sha256"):
            raise ValueError("Low-memory Beam base-plan hash mismatch")
        base = json.loads(base_path.read_text(encoding="utf-8"))
        return _deep_merge(base, raw)
    return raw


def validate_plan(plan: dict[str, Any], *, plan_path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    if plan.get("schema_version") == V115_RESUME_V114_SCHEMA:
        return _validate_v115_resume_v114_plan(plan, plan_path=plan_path)
    if plan.get("schema_version") == V114_LOWMEM_32GB_SCHEMA:
        return _validate_v114_lowmem_32gb_plan(plan, plan_path=plan_path)
    if plan.get("schema_version") == LOWMEM_32GB_SCHEMA:
        return _validate_lowmem_32gb_plan(plan, plan_path=plan_path)
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


def resolve_accumulator_spill_format(stage: dict[str, Any]) -> str:
    """Resolve the spill encoding from an explicit contract with v113 compatibility."""
    declared = stage.get("accumulator_spill_format")
    if declared is not None:
        value = str(declared)
        if value not in ACCUMULATOR_SPILL_FORMATS:
            raise ValueError(f"Unsupported accumulator spill format: {value!r}")
        return value
    if stage.get("stage_id") == LOWMEM_32GB_STAGE_ID:
        return STREAMING_ACCUMULATOR_SPILL_FORMAT
    return LEGACY_ACCUMULATOR_SPILL_FORMAT


def stage_by_id(plan: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in plan["stages"]:
        if stage["stage_id"] == stage_id:
            return stage
    raise ValueError(f"Unknown Beam Search stage: {stage_id}")


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def resolve_actual_data_hashes(required_keys: set[str] | None = None) -> dict[str, str]:
    actual = {
        "action_data_hash": action_data_hash(root=ROOT),
        "party_config_hash": party_config_hash(root=ROOT),
    }
    for key, path in HASH_FILE_PATHS.items():
        if required_keys is None or key in required_keys:
            actual[key] = sha256_file(path)
    return actual


def resolve_plan_data_hashes(plan: dict[str, Any]) -> dict[str, str]:
    if plan.get("schema_version") in {LOWMEM_32GB_SCHEMA, V114_LOWMEM_32GB_SCHEMA, V115_RESUME_V114_SCHEMA}:
        return resolve_actual_data_hashes(
            {
                "direct_action_manifest_sha256",
                "direct_action_manifest_copy_sha256",
                "bc_npz_sha256",
                "manual_route_raw_sha256",
            }
        )
    return resolve_actual_data_hashes()


def _validate_lowmem_32gb_plan(plan: dict[str, Any], *, plan_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    for key, expected in {
        "schema_version": LOWMEM_32GB_SCHEMA,
        "candidate": "113",
        "algorithm": EXPECTED_ALGORITHM,
        "objective": EXPECTED_OBJECTIVE,
        "party": EXPECTED_PARTY,
        "initial_active_character": EXPECTED_INITIAL_ACTIVE,
        "curriculum_reset_mode": EXPECTED_CURRICULUM,
        "route_similarity_objective": False,
        "bc_ppo_policy_guidance": False,
        "manual_route_guidance": False,
        "global_optimum_proven": False,
    }.items():
        if plan.get(key) != expected:
            errors.append(f"{key} {plan.get(key)!r} != {expected!r}")
    inheritance = plan.get("inherits_contracts_from", {})
    if inheritance.get("path") != "data/beam_search_plan_v111.json" or inheritance.get("sha256") != "b504def4e0c1da82ef2a6024d19ccac76fe175df51899e50d12f3bff99a17998":
        errors.append("inherits_contracts_from must pin the verified v111 plan")
    observation = plan.get("observation_contract", {})
    for key, expected in {"version": "slot_generic_mechanics_v5", "shape": 314, "policy_action_count": 25, "max_policy_action_slots": 32}.items():
        if observation.get(key) != expected:
            errors.append(f"observation_contract.{key} {observation.get(key)!r} != {expected!r}")
    stages = plan.get("stages")
    expected_stage = {
        "stage_id": LOWMEM_32GB_STAGE_ID,
        "combat_duration": 120.0,
        "time_bucket_width": 0.5,
        "beam_width": 1792,
        "global_damage_quota": 896,
        "diversity_retention_quota": 896,
        "max_states_per_diversity_key": 8,
        "maximum_expansions": 5000000,
        "checkpoint_interval_expansions": 100000,
        "limit_check_interval_expansions": 256,
        "wall_clock_budget_seconds": 36000,
        "wall_clock_limit_seconds": 36000.0,
        "memory_budget_bytes": 23622320128,
        "max_unique_fingerprints_per_destination_bucket": 16384,
        "destination_accumulator_unique_fingerprint_bound": 16384,
        "in_memory_accumulator_candidate_limit": 4096,
        "disk_spill_enabled": True,
    }
    if not isinstance(stages, list) or len(stages) != 1:
        errors.append("low-memory plan must contain exactly one stage")
    else:
        for key, expected in expected_stage.items():
            if stages[0].get(key) != expected:
                errors.append(f"{LOWMEM_32GB_STAGE_ID}.{key} {stages[0].get(key)!r} != {expected!r}")
    policy = plan.get("initial_execution_policy", {})
    if policy.get("first_run_max_expansions") != 3000000 or policy.get("plan_maximum_expansions") != 5000000 or policy.get("extension_requires_external_review") is not True:
        errors.append("initial_execution_policy must require reviewed 3M then optional 5M resume")
    output = plan.get("output_contract", {})
    if output.get("canonical_output_root") != LOWMEM_32GB_OUTPUT_ROOT:
        errors.append("low-memory canonical output root mismatch")
    if FORBIDDEN_64GB_OUTPUT_ROOT not in output.get("forbidden_resume_or_output_roots", []):
        errors.append("old 64GB output root must be forbidden")
    memory = plan.get("memory_estimate_contract", {})
    for key, expected in {
        "destination_bucket_insertion_order_independent": True,
        "destination_bucket_partition_merge_independent": True,
        "destination_accumulator_spill_policy": "atomic_compressed_json_gz_chunks_hash_validated_resume_exact",
        "destination_accumulator_checkpoint_manifest": "compact_manifest_with_paths_sha256_counts_and_metrics_no_node_payloads",
        "compact_cli_output_contract": "stdout_summary_only_no_frontier_nodes_route_store_accumulator_payloads_or_timelines",
        "limit_check_interval_expansions": 256,
        "hard_memory_budget_required": True,
        "windows_page_file_assumed": False,
    }.items():
        if memory.get(key) != expected:
            errors.append(f"memory_estimate_contract.{key} {memory.get(key)!r} != {expected!r}")
    resume = plan.get("resume_contract", {})
    for key in ("atomic_frontier_writes", "partial_node_action_cursor", "dirty_bucket_checkpoint_writes", "plan_hash_validated", "stage_hash_validated", "actual_data_hashes_validated"):
        if resume.get(key) is not True:
            errors.append(f"resume_contract.{key} must be true")
    hashes = plan.get("data_contract_hashes", {})
    declared_hashes = {
        "action_data_hash": EXPECTED_ACTION_DATA_HASH,
        "party_config_hash": EXPECTED_PARTY_CONFIG_HASH,
        "direct_action_manifest_sha256": EXPECTED_DIRECT_ACTION_MANIFEST_SHA256,
        "bc_npz_sha256": EXPECTED_BC_NPZ_SHA256,
        "bc_model_sha256": EXPECTED_BC_MODEL_SHA256,
        "prior_ppo_model_sha256": EXPECTED_PPO_MODEL_SHA256,
        "manual_route_raw_sha256": EXPECTED_ROUTE_SHA256,
    }
    for key, expected in declared_hashes.items():
        if hashes.get(key) != expected:
            errors.append(f"{key} {hashes.get(key)!r} != {expected!r}")
    actual = resolve_plan_data_hashes(plan)
    for key in ("action_data_hash", "party_config_hash", "direct_action_manifest_sha256", "bc_npz_sha256", "manual_route_raw_sha256"):
        if actual.get(key) != declared_hashes[key]:
            errors.append(f"actual {key} {actual.get(key)!r} != {declared_hashes[key]!r}")
    if actual.get("direct_action_manifest_copy_sha256") != EXPECTED_DIRECT_ACTION_MANIFEST_SHA256:
        errors.append("actual direct-action manifest copy hash mismatch")
    if plan.get("diversity_key_schema", {}).get("declared_character_mechanic_fields") != diversity_quantization_contract()["declared_character_mechanic_fields"]:
        errors.append("low-memory diversity mechanic fields do not match runtime")
    serialized = json.dumps(plan, sort_keys=True).lower()
    for forbidden in ("manual_action_sequence", "selected_policy_actions", "expected_resolved_actions"):
        if forbidden in serialized:
            errors.append(f"plan contains forbidden policy guidance: {forbidden}")
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "ok",
        "plan_path": project_relative(plan_path),
        "plan_sha256": sha256_file(plan_path),
        "stage_ids": [LOWMEM_32GB_STAGE_ID],
        "future_execution_only": True,
        "actual_data_hashes": actual,
    }


def _validate_v114_lowmem_32gb_plan(plan: dict[str, Any], *, plan_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    for key, expected in {
        "schema_version": V114_LOWMEM_32GB_SCHEMA,
        "candidate": 114,
        "algorithm": EXPECTED_ALGORITHM,
        "objective": EXPECTED_OBJECTIVE,
        "party": EXPECTED_PARTY,
        "initial_active_character": EXPECTED_INITIAL_ACTIVE,
        "curriculum_reset_mode": EXPECTED_CURRICULUM,
        "combat_duration": 120.0,
        "route_similarity_objective": False,
        "bc_ppo_policy_guidance": False,
        "manual_route_guidance": False,
        "global_optimum_proven": False,
    }.items():
        if plan.get(key) != expected:
            errors.append(f"{key} {plan.get(key)!r} != {expected!r}")
    inheritance = plan.get("inherits_contracts_from", {})
    if inheritance != {
        "path": "data/beam_search_plan_v111.json",
        "sha256": "b504def4e0c1da82ef2a6024d19ccac76fe175df51899e50d12f3bff99a17998",
    }:
        errors.append("inherits_contracts_from must pin the verified v111 plan")
    observation = plan.get("observation_contract", {})
    for key, expected in {
        "version": "slot_generic_mechanics_v5",
        "shape": 314,
        "policy_action_count": 25,
        "max_policy_action_slots": 32,
    }.items():
        if observation.get(key) != expected:
            errors.append(f"observation_contract.{key} {observation.get(key)!r} != {expected!r}")
    expected_stage = {
        "stage_id": "full_120s_lowmem_32gb_v114",
        "combat_duration": 120.0,
        "time_bucket_width": 0.5,
        "beam_width": 1792,
        "global_damage_quota": 896,
        "diversity_retention_quota": 896,
        "max_states_per_diversity_key": 8,
        "maximum_expansions": 5000000,
        "checkpoint_interval_expansions": 100000,
        "limit_check_interval_expansions": 256,
        "wall_clock_budget_seconds": 36000,
        "wall_clock_limit_seconds": 36000.0,
        "memory_budget_bytes": 23622320128,
        "max_unique_fingerprints_per_destination_bucket": 16384,
        "destination_accumulator_unique_fingerprint_bound": 16384,
        "in_memory_accumulator_candidate_limit": 4096,
        "disk_spill_enabled": True,
        "accumulator_spill_format": STREAMING_ACCUMULATOR_SPILL_FORMAT,
    }
    stages = plan.get("stages")
    if not isinstance(stages, list) or len(stages) != 1:
        errors.append("v114 low-memory plan must contain exactly one stage")
    else:
        for key, expected in expected_stage.items():
            if stages[0].get(key) != expected:
                errors.append(f"full_120s_lowmem_32gb_v114.{key} {stages[0].get(key)!r} != {expected!r}")
        try:
            resolved_spill_format = resolve_accumulator_spill_format(stages[0])
        except ValueError as error:
            errors.append(str(error))
        else:
            if resolved_spill_format != STREAMING_ACCUMULATOR_SPILL_FORMAT:
                errors.append("candidate-114 low-memory stage must resolve to deterministic streaming spill")
    policy = plan.get("initial_execution_policy", {})
    if policy.get("first_run_max_expansions") != 3000000 or policy.get("plan_maximum_expansions") != 5000000:
        errors.append("initial_execution_policy must preserve reviewed 3M/5M limits")
    output = plan.get("output_contract", {})
    if output.get("canonical_output_root") != "results/beam_search_v114_lowmem_32gb":
        errors.append("candidate-114 canonical output root mismatch")
    forbidden = set(output.get("forbidden_resume_or_output_roots", []))
    required_forbidden = {"results/beam_search_v111_full_120s", "results/beam_search_v113_lowmem_32gb"}
    if not required_forbidden.issubset(forbidden):
        errors.append("candidate-114 plan must forbid both v111 and interrupted v113 roots")
    transition = plan.get("transition_contract", {})
    for key, expected in {
        "version": "v114",
        "generic_swap_action_time": 0.0,
        "generic_swap_combat_time_cost": 0.0,
        "generic_swap_source_status": "user_approved_benchmark_assumption_after_workbook_and_web_review",
        "swap_reentry_cooldown_seconds": 1.0,
        "swap_reentry_cooldown_clock": "combat_time",
        "aemeath_outro_implementation_version": "implemented_v114",
    }.items():
        if transition.get(key) != expected:
            errors.append(f"transition_contract.{key} {transition.get(key)!r} != {expected!r}")
    hashes = plan.get("data_contract_hashes", {})
    actual = resolve_plan_data_hashes(plan)
    for key in ("action_data_hash", "party_config_hash", "direct_action_manifest_sha256", "bc_npz_sha256", "manual_route_raw_sha256"):
        if hashes.get(key) != actual.get(key):
            errors.append(f"actual {key} {actual.get(key)!r} != declared {hashes.get(key)!r}")
    direct_paths = {
        "transition_config_sha256": ROOT / "data/transition_config.json",
        "buffs_sha256": ROOT / "data/buffs.json",
        "manual_model_comparison_v114_sha256": ROOT / "results/manual_model_comparison_v114.json",
        "current_best_v114_result_sha256": ROOT / "results/transition_contract_v114_model_reevaluation/evaluations/guarded_ppo_v109__bc_conservative_seed_11__step_000090000.zip.json",
    }
    for key, path in direct_paths.items():
        if not path.exists() or hashes.get(key) != sha256_file(path):
            errors.append(f"{key} does not match {project_relative(path)}")
    comparison = plan.get("comparison_reference", {})
    for path_key, hash_key in (("path", "sha256"), ("current_best_result_path", "current_best_result_sha256")):
        path = ROOT / str(comparison.get(path_key, ""))
        if not path.exists() or comparison.get(hash_key) != sha256_file(path):
            errors.append(f"comparison_reference.{path_key}/{hash_key} mismatch")
    if plan.get("diversity_key_schema", {}).get("declared_character_mechanic_fields") != diversity_quantization_contract()["declared_character_mechanic_fields"]:
        errors.append("candidate-114 diversity mechanic fields do not match runtime")
    serialized = json.dumps(plan, sort_keys=True).lower()
    for forbidden_key in ("manual_action_sequence", "selected_policy_actions", "expected_resolved_actions"):
        if forbidden_key in serialized:
            errors.append(f"plan contains forbidden policy guidance: {forbidden_key}")
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "ok",
        "plan_path": project_relative(plan_path),
        "plan_sha256": sha256_file(plan_path),
        "stage_ids": ["full_120s_lowmem_32gb_v114"],
        "stage_accumulator_spill_formats": {
            "full_120s_lowmem_32gb_v114": resolve_accumulator_spill_format(stages[0]),
        },
        "future_execution_only": True,
        "actual_data_hashes": actual,
    }


def _validate_v115_resume_v114_plan(plan: dict[str, Any], *, plan_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    legacy = copy.deepcopy(plan)
    legacy["schema_version"] = V114_LOWMEM_32GB_SCHEMA
    legacy["candidate"] = 114
    legacy["initial_execution_policy"]["plan_maximum_expansions"] = 5000000
    legacy["stages"][0]["maximum_expansions"] = 5000000
    legacy["stages"][0].pop("result_scope", None)
    for key in ("resume_extension_contract", "comparison_incumbent_contract", "result_scope_contract", "execution_contract", "source_checkpoint_contract"):
        legacy.pop(key, None)
    _validate_v114_lowmem_32gb_plan(legacy, plan_path=V114_LOWMEM_32GB_PLAN_PATH)
    if plan.get("candidate") != 115:
        errors.append("candidate must be 115")
    execution = plan.get("execution_contract", {})
    expected_execution = {
        "low_memory_32gb": True,
        "hard_memory_budget_required": True,
        "canonical_output_root_required_for_resume": True,
        "reviewed_memory_budget_bytes": 23622320128,
        "memory_budget_cli_policy": "may_lower_never_raise",
        "safety_gates_plan_capability_driven": True,
    }
    for key, expected in expected_execution.items():
        if execution.get(key) != expected:
            errors.append(f"execution_contract.{key} mismatch")
    stage = plan.get("stages", [{}])[0]
    if stage.get("maximum_expansions") != 6500000:
        errors.append("maximum_expansions must be 6500000")
    if stage.get("result_scope") != "completed_120s_project_comparison":
        errors.append("stage result_scope must be completed_120s_project_comparison")
    scope = plan.get("result_scope_contract", {})
    if scope.get("accepted_values") != ["completed_120s_project_comparison", "calibration_horizon_only", "smoke_only"]:
        errors.append("result_scope_contract accepted values mismatch")
    policy = plan.get("initial_execution_policy", {})
    if policy.get("plan_maximum_expansions") != 6500000 or policy.get("recommended_resume_target") != 6500000:
        errors.append("candidate-115 reviewed/recommended maximum must be 6500000")
    resume = plan.get("resume_extension_contract", {})
    expected_resume = {
        "enabled": True,
        "source_plan_path": "data/beam_search_plan_v114_32gb.json",
        "source_plan_sha256": "e70826d0040444f834398d55c922aacb4ee5b484bc6ef2e75ca5a0ad603bc18c",
        "source_stage_id": "full_120s_lowmem_32gb_v114",
        "source_checkpoint_expansions": 3000000,
        "source_search_state_sha256": "f1ac52b960465a7ea71ea8495b1c1f2d89a79766d5cdf2f6ad3e4872d2e25630",
        "receipt_path": "results/beam_search_v114_3m_resume_extension_v115_receipt.json",
        "allowed_stage_differences": ["maximum_expansions", "result_scope"],
        "minimum_new_maximum_expansions": 5000001,
        "maximum_new_maximum_expansions": 6500000,
    }
    for key, expected in expected_resume.items():
        if resume.get(key) != expected:
            errors.append(f"resume_extension_contract.{key} mismatch")
    if sha256_file(ROOT / expected_resume["source_plan_path"]) != expected_resume["source_plan_sha256"]:
        errors.append("source v114 plan hash mismatch")
    checkpoint = plan.get("source_checkpoint_contract", {})
    expected_checkpoint = {
        "reviewed_inventory_path": "results/beam_search_v114_3m_reviewed_file_inventory_v115.json",
        "reviewed_inventory_file_sha256": "9e4fc52836ba4986ba1d78c544120657ae1fb4593520fceabc71d2b527bf6a5a",
        "reviewed_inventory_entry_digest_sha256": "0bb00535354717d05ae1761fe6522bcc5129cc598cc8aaf072843626a7d43f15",
        "external_review_inventory_manifest_sha256": "35a52b044856327790dcd993fe524b4144214db31f4338fda154d824f2574bee",
        "file_count": 649,
        "total_bytes": 1752618157,
        "best_route_sha256": "0c478c21701f323166362c99cd99d5cdc63870f3c42745d4209afcbc9e254f24",
        "execution_result_sha256": "21a9c4014e5b040b07c2034913b24908229ffa578e6f55d4dc956bd622eb48cc",
        "final_summary_sha256": "3b0db39bd2ebb64559c29bfe1484ac7e053badf41846744fc90af951eb92f5f6",
        "leaderboard_sha256": "e9f2e044dc0a837a52881a4aa263c9041aea9f77e8c9a8236cbce7c3fc193397",
        "search_state_sha256": "f1ac52b960465a7ea71ea8495b1c1f2d89a79766d5cdf2f6ad3e4872d2e25630",
        "log_sha256": "64838ae7cf45743ba9d55251761e9c03ab9dbda3128995c2d20dfec4b865ce9a",
        "best_partial_source_path": "execution_result.json",
        "best_partial_combat_time": 67.48333333333329,
        "best_partial_current_time": 107.75000000000001,
        "best_partial_total_damage": 2850679.8061139295,
        "best_partial_action_count": 92,
    }
    for key, expected in expected_checkpoint.items():
        if checkpoint.get(key) != expected:
            errors.append(f"source_checkpoint_contract.{key} mismatch")
    inventory_path = ROOT / str(checkpoint.get("reviewed_inventory_path", ""))
    if not inventory_path.is_file() or sha256_file(inventory_path) != checkpoint.get("reviewed_inventory_file_sha256"):
        errors.append("reviewed checkpoint inventory file mismatch")
    incumbent = plan.get("comparison_incumbent_contract", {})
    required_incumbent = {
        "model_path": "models/guarded_ppo_v109/bc_conservative_seed_11/step_000090000.zip",
        "model_sha256": "dc437ff4e03b50001e9829550b1e52ff0f503d963ec3433a7adf88848b5e3073",
        "result_path": "results/transition_contract_v114_model_reevaluation/evaluations/guarded_ppo_v109__bc_conservative_seed_11__step_000090000.zip.json",
        "result_sha256": "8c0c47c3d266ba13d3e4658446a8b86b6c084678610baff61f94753190359f59",
        "total_damage": 5276844.358692044,
        "dps": 43973.70298910037,
        "selected_sequence_sha256": "27920c26c93bc51aacb964211062b301a2af16b899e2bbafc442edca17e72c54",
        "resolved_sequence_sha256": "350df3b0df184b5d9e8c5cecffef7893ddb53f6d31eeaf864bf7c61fb71590f0",
    }
    for key, expected in required_incumbent.items():
        if incumbent.get(key) != expected:
            errors.append(f"comparison_incumbent_contract.{key} mismatch")
    from search.beam_reporting import load_project_comparison_incumbent
    try:
        load_project_comparison_incumbent(plan)
    except ValueError as error:
        errors.append(str(error))
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "ok",
        "plan_path": project_relative(plan_path),
        "plan_sha256": sha256_file(plan_path),
        "stage_ids": ["full_120s_lowmem_32gb_v114"],
        "result_scope": stage["result_scope"],
        "recommended_resume_target": 6500000,
        "future_execution_only": True,
        "actual_data_hashes": resolve_plan_data_hashes(plan),
    }


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


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
