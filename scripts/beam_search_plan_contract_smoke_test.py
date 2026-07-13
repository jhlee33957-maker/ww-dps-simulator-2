from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import DEFAULT_PLAN_PATH, load_plan, validate_plan  # noqa: E402


def main() -> None:
    plan = load_plan(DEFAULT_PLAN_PATH)
    result = validate_plan(plan, plan_path=DEFAULT_PLAN_PATH)
    assert result["status"] == "ok"
    assert result["stage_ids"] == ["calibration_30s", "full_120s"]
    assert result["future_execution_only"] is True
    assert result["actual_data_hashes"]["action_data_hash"] == "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1"
    assert result["actual_data_hashes"]["party_config_hash"] == "bd106ba1c0f5581436c35fea736a00fd6ad92b131f8b43ba8cf1e3dc89cbcb11"
    serialized = DEFAULT_PLAN_PATH.read_text(encoding="utf-8").lower()
    for forbidden in ("manual_action_sequence", "selected_policy_actions", "expected_resolved_actions"):
        assert forbidden not in serialized
    mutations = [
        ("route_similarity_objective", lambda item: item.__setitem__("route_similarity_objective", True)),
        ("stage_wall_clock", lambda item: item["stages"][0].__setitem__("wall_clock_limit_seconds", 999.0)),
        ("stage_memory", lambda item: item["stages"][0].__setitem__("memory_budget_bytes", 1)),
        ("limit_interval", lambda item: item["stages"][0].__setitem__("limit_check_interval_expansions", 128)),
        ("mechanic_field_removed", lambda item: item["diversity_key_schema"]["declared_character_mechanic_fields"]["aemeath"].remove("sync_strike_window_remaining")),
        ("mechanic_encoder_changed", lambda item: item["diversity_key_schema"]["declared_mechanic_field_encoders"]["aemeath"]["sync_strike_window_remaining"].__setitem__("band", 5.0)),
        ("memory_pending_bound", lambda item: item["memory_estimate_contract"].__setitem__("pending_bucket_node_bound", "unbounded")),
        ("memory_live_formula", lambda item: item["memory_estimate_contract"].__setitem__("live_node_budget_formula", "unknown")),
        ("safe_default_budget", lambda item: item["memory_estimate_contract"].__setitem__("limit_check_interval_expansions", 4096)),
        ("reporting_horizon_status", lambda item: item["final_reporting_contract"].__setitem__("short_horizon_numeric_reference_ranking", True)),
        ("checkpoint_contract", lambda item: item["checkpoint_contract"].__setitem__("dirty_bucket_only_between_forced_writes", False)),
        ("resume_contract", lambda item: item["resume_contract"].__setitem__("partial_node_action_cursor", False)),
    ]
    for label, mutate in mutations:
        changed = copy.deepcopy(plan)
        mutate(changed)
        try:
            validate_plan(changed, plan_path=DEFAULT_PLAN_PATH)
        except ValueError:
            continue
        raise AssertionError(f"mutated plan was accepted: {label}")
    print("beam_search_plan_contract_smoke_test ok")


if __name__ == "__main__":
    main()
