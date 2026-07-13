from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import DEFAULT_PLAN_PATH, load_plan, validate_plan  # noqa: E402
from search.beam_search import _memory_estimate_for_stage  # noqa: E402


def main() -> None:
    plan = load_plan(DEFAULT_PLAN_PATH)
    validate_plan(plan, plan_path=DEFAULT_PLAN_PATH)
    estimate = _memory_estimate_for_stage(plan, plan["stages"][0])
    bound = estimate["derived_concurrent_bucket_bound"]
    assert bound["max_resolved_combat_time_cost"] == 2.6666666666666665
    assert bound["max_resolved_combat_time_cost_action_id"] == "lynae_kaleidoscopic_mid_air_heavy"
    assert bound["required_concurrent_bucket_count"] == 9
    assert estimate["concurrent_bucket_count"] >= 9
    assert estimate["conservative_total_bytes"] > estimate["payload_bytes"]
    undersized = copy.deepcopy(plan)
    undersized["memory_estimate_contract"]["concurrent_bucket_count"] = 3
    try:
        validate_plan(undersized, plan_path=DEFAULT_PLAN_PATH)
    except ValueError as exc:
        assert "concurrent_bucket_count" in str(exc)
    else:
        raise AssertionError("undersized concurrent-bucket memory bound was accepted")
    print("beam_search_memory_bound_contract_smoke_test ok")


if __name__ == "__main__":
    main()
