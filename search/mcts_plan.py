from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from search.search_state_codec import canonical_json_bytes


ALGORITHM = "state_uct_mast_v117"
OBJECTIVE = "deterministic_completed_120s_total_damage"
HARD_MEMORY_BUDGET = 23_622_320_128
REQUIRED_HASHES = {
    "action_data_hash": "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1",
    "party_config_hash": "baff722d9ce79cf7f57891c439b7b3fd746ad76e779e4d582eaa51802eba2684",
    "transition_config_sha256": "210538d4bf99789d0af08ecff5fb76dc3f472f5b170a144d9f1b3b1f46116b9c",
    "buffs_sha256": "fe8b8fc63e8b9a3405a61ebe08a2cafa13f94dd4af91d1670b968df727cb554d",
    "direct_action_manifest_sha256": "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d",
}


def load_mcts_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_mcts_plan(payload)
    payload["_plan_path"] = path.as_posix()
    payload["_plan_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return payload


def stage_contract_hash(plan: dict[str, Any], stage: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes({
        "algorithm": plan["algorithm"], "objective": plan["objective"],
        "uct": plan["uct"], "progressive_widening": plan["progressive_widening"],
        "mast": plan["mast"], "reward": plan["reward"], "stage": stage,
        "data_contract_hashes": plan["data_contract_hashes"],
    })).hexdigest()


def validate_mcts_plan(plan: dict[str, Any]) -> None:
    exact = {
        "schema_version": "mcts_plan_v117_32gb", "candidate": 117, "algorithm": ALGORITHM,
        "objective": OBJECTIVE, "global_optimum_proven": False, "manual_route_guidance": False,
        "bc_ppo_policy_guidance": False, "beam_policy_guidance": False, "beam_route_guidance": False,
        "party": "aemeath_mornye_lynae_enabled_test_party", "initial_active_character": "aemeath",
        "observation_version": "slot_generic_mechanics_v5", "observation_shape": 314,
        "policy_action_count": 25, "max_policy_action_slots": 32,
    }
    for key, value in exact.items():
        if plan.get(key) != value:
            raise ValueError(f"MCTS plan {key} mismatch: {plan.get(key)!r} != {value!r}")
    if plan.get("uct") != {"exploration_constant": 2.0 ** 0.5, "backup": "mean_terminal_reward", "unvisited_priority": True}:
        raise ValueError("MCTS UCT contract mismatch")
    if plan.get("reward") != {"terminal_scale": 6000000.0, "clip": False, "partial_reward": False}:
        raise ValueError("MCTS reward contract mismatch")
    if plan.get("progressive_widening") != {"coefficient": 2.0, "exponent": 0.5, "minimum_children": 1, "maximum_new_children_per_simulation": 1}:
        raise ValueError("MCTS progressive-widening contract mismatch")
    if plan.get("mast") != {"policy": "mast_epsilon_greedy_v117", "uniform_warmup_simulations": 1000, "epsilon": 0.2, "minimum_visits": 4, "context": "active_character_id+policy_action_id"}:
        raise ValueError("MCTS MAST contract mismatch")
    execution = plan.get("execution_contract") or {}
    required_execution = {"low_memory_32gb": True, "hard_memory_budget_required": True, "memory_budget_cli_policy": "may_lower_never_raise", "single_process_deterministic": True, "multiworker": False, "page_file_assumed": False}
    if execution != required_execution:
        raise ValueError("MCTS execution contract mismatch")
    if plan.get("data_contract_hashes") != REQUIRED_HASHES:
        raise ValueError("MCTS data-contract hashes mismatch")
    stages = plan.get("stages")
    if not isinstance(stages, list) or len(stages) != 1:
        raise ValueError("Candidate 117 must contain exactly one executable MCTS stage")
    stage = stages[0]
    required_stage = {
        "stage_id": "calibration_20k_seed_117001", "seed": 117001, "combat_duration": 120.0,
        "maximum_simulations": 20000, "maximum_nodes": 25001, "maximum_actions_per_simulation": 512,
        "maximum_consecutive_zero_time_actions": 32, "snapshot_stride": 8,
        "checkpoint_interval_simulations": 1000, "limit_check_interval_simulations": 64,
        "completed_route_leaderboard_size": 128, "memory_budget_bytes": HARD_MEMORY_BUDGET,
        "soft_memory_target_bytes": 21474836480, "wall_clock_budget_seconds": 14400,
        "decoded_snapshot_cache_entries": 128, "decoded_snapshot_cache_maximum_bytes": 536870912,
        "canonical_output_root": "results/mcts_v117_32gb/calibration_20k_seed_117001",
    }
    for key, value in required_stage.items():
        if stage.get(key) != value:
            raise ValueError(f"MCTS stage {key} mismatch: {stage.get(key)!r} != {value!r}")


def lowered_memory_budget(configured: int, requested: int | None) -> int:
    if requested is None:
        return int(configured)
    if requested > configured:
        raise ValueError("CLI memory budget may lower but never raise the configured 22 GiB hard limit")
    return int(requested)
