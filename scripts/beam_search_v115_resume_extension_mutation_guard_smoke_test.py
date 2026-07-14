from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import V115_RESUME_V114_PLAN_PATH, load_plan, validate_plan
from search.beam_search import _resume_extension_plan_compatible


def main() -> None:
    plan = load_plan(V115_RESUME_V114_PLAN_PATH)
    state_path = ROOT / "results/beam_search_v114_lowmem_32gb/search_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        state = {"plan_sha256": plan["resume_extension_contract"]["source_plan_sha256"], "expansions": 3000000, "stage": copy.deepcopy(plan["stages"][0])}
        state["stage"].pop("result_scope", None); state["stage"]["maximum_expansions"] = 3000000
    assert _resume_extension_plan_compatible(state, plan)
    for key, value in (("beam_width", 1), ("global_damage_quota", 1), ("time_bucket_width", 1.0), ("memory_budget_bytes", 1), ("accumulator_spill_format", "bad"), ("stage_id", "bad")):
        bad = copy.deepcopy(plan); bad["stages"][0][key] = value
        assert not _resume_extension_plan_compatible(state, bad), key
    for maximum in (3000000, 6500001):
        bad = copy.deepcopy(plan); bad["stages"][0]["maximum_expansions"] = maximum
        assert not _resume_extension_plan_compatible(state, bad)
    for mutation in ("action_data_hash", "transition_config_sha256", "buffs_sha256"):
        bad = copy.deepcopy(plan); bad["data_contract_hashes"][mutation] = "0" * 64
        try:
            validate_plan(bad, plan_path=V115_RESUME_V114_PLAN_PATH)
        except ValueError:
            pass
        else:
            raise AssertionError(mutation)
    print("beam_search_v115_resume_extension_mutation_guard_smoke_test ok")


if __name__ == "__main__":
    main()
