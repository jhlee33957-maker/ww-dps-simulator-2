from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import LOWMEM_32GB_PLAN_PATH, load_plan, sha256_file, validate_plan


EXPECTED_PLAN_SHA256 = "ffd9ce47ec9b92b2c4b59f295d50d0ce5204fcba577af0f78b9fa917b19b291d"
EXPECTED_V111_SHA256 = "b504def4e0c1da82ef2a6024d19ccac76fe175df51899e50d12f3bff99a17998"


def main() -> int:
    plan = load_plan(LOWMEM_32GB_PLAN_PATH)
    result = validate_plan(plan, plan_path=LOWMEM_32GB_PLAN_PATH)
    assert result["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert sha256_file(Path("data/beam_search_plan_v111.json")) == EXPECTED_V111_SHA256
    exact_mutations = (
        ("beam_width", 1791),
        ("global_damage_quota", 895),
        ("diversity_retention_quota", 897),
        ("memory_budget_bytes", 23622320127),
        ("wall_clock_budget_seconds", 35999),
        ("maximum_expansions", 4999999),
        ("combat_duration", 119.5),
        ("in_memory_accumulator_candidate_limit", 4095),
        ("destination_accumulator_unique_fingerprint_bound", 16383),
        ("disk_spill_enabled", False),
    )
    for key, value in exact_mutations:
        mutated = copy.deepcopy(plan)
        mutated["stages"][0][key] = value
        try:
            validate_plan(mutated, plan_path=LOWMEM_32GB_PLAN_PATH)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Mutation unexpectedly passed: {key}")
    for key in ("manual_route_guidance", "bc_ppo_policy_guidance", "route_similarity_objective", "global_optimum_proven"):
        mutated = copy.deepcopy(plan)
        mutated[key] = True
        try:
            validate_plan(mutated, plan_path=LOWMEM_32GB_PLAN_PATH)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Guidance mutation unexpectedly passed: {key}")
    print("beam_search_lowmem_32gb_plan_contract_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
