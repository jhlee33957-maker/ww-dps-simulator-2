from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import V115_RESUME_V114_PLAN_PATH, load_plan, validate_plan


def main() -> None:
    plan = load_plan(V115_RESUME_V114_PLAN_PATH)
    result = validate_plan(plan, plan_path=V115_RESUME_V114_PLAN_PATH)
    stage = plan["stages"][0]
    assert result["status"] == "ok" and result["recommended_resume_target"] == 6500000
    assert stage["maximum_expansions"] == 6500000
    assert plan["output_contract"]["canonical_output_root"] == "results/beam_search_v114_lowmem_32gb"
    assert plan["resume_extension_contract"]["source_search_state_sha256"] == "f1ac52b960465a7ea71ea8495b1c1f2d89a79766d5cdf2f6ad3e4872d2e25630"
    assert plan["resume_extension_contract"]["allowed_stage_differences"] == ["maximum_expansions", "result_scope"]
    assert plan["execution_contract"]["low_memory_32gb"] is True
    assert plan["execution_contract"]["hard_memory_budget_required"] is True
    assert plan["source_checkpoint_contract"]["file_count"] == 649
    assert plan["source_checkpoint_contract"]["total_bytes"] == 1752618157
    print(f"beam_search_v115_resume_extension_plan_contract_smoke_test ok plan_sha256={result['plan_sha256']}")


if __name__ == "__main__":
    main()
