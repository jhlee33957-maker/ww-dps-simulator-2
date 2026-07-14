from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from search.beam_plan import (
    LEGACY_ACCUMULATOR_SPILL_FORMAT,
    STREAMING_ACCUMULATOR_SPILL_FORMAT,
    V114_LOWMEM_32GB_PLAN_PATH,
    load_plan,
    resolve_accumulator_spill_format,
    sha256_file,
    validate_plan,
)


def main() -> None:
    plan = load_plan(V114_LOWMEM_32GB_PLAN_PATH)
    result = validate_plan(plan, plan_path=V114_LOWMEM_32GB_PLAN_PATH)
    assert result["stage_ids"] == ["full_120s_lowmem_32gb_v114"]
    assert result["stage_accumulator_spill_formats"] == {
        "full_120s_lowmem_32gb_v114": STREAMING_ACCUMULATOR_SPILL_FORMAT,
    }
    assert resolve_accumulator_spill_format(plan["stages"][0]) == STREAMING_ACCUMULATOR_SPILL_FORMAT
    assert plan["output_contract"]["canonical_output_root"] == "results/beam_search_v114_lowmem_32gb"
    assert "results/beam_search_v113_lowmem_32gb" in plan["output_contract"]["forbidden_resume_or_output_roots"]
    assert plan["execution_boundary"]["candidate_114_runs_3m_search"] is False
    assert plan["execution_boundary"]["candidate_114_runs_5m_search"] is False
    assert plan["execution_boundary"]["candidate_114_runs_training"] is False
    marker_path = ROOT / "results/beam_search_v113_lowmem_32gb/CONTRACT_INCOMPATIBLE_WITH_V114.json"
    if marker_path.exists():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        assert marker["resume_allowed"] is False
        assert marker["status"] == "preserved_incompatible_interrupted_output"
    else:
        # Slim v114 runtime intentionally excludes the complete interrupted root.
        assert not (ROOT / "results/beam_search_v113_lowmem_32gb").exists()
    for key, value in (
        ("beam_width", 1791),
        ("memory_budget_bytes", 23622320127),
        ("maximum_expansions", 4999999),
        ("in_memory_accumulator_candidate_limit", 4095),
        ("disk_spill_enabled", False),
    ):
        mutated = copy.deepcopy(plan)
        mutated["stages"][0][key] = value
        try:
            validate_plan(mutated, plan_path=V114_LOWMEM_32GB_PLAN_PATH)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Mutation unexpectedly passed: {key}")
    for mutation in ("removed", LEGACY_ACCUMULATOR_SPILL_FORMAT, "unknown_spill_format"):
        mutated = copy.deepcopy(plan)
        if mutation == "removed":
            mutated["stages"][0].pop("accumulator_spill_format")
        else:
            mutated["stages"][0]["accumulator_spill_format"] = mutation
        try:
            validate_plan(mutated, plan_path=V114_LOWMEM_32GB_PLAN_PATH)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Spill-format mutation unexpectedly passed: {mutation}")
    renamed = copy.deepcopy(plan["stages"][0])
    renamed["stage_id"] = "renamed_v114_stage"
    assert resolve_accumulator_spill_format(renamed) == STREAMING_ACCUMULATOR_SPILL_FORMAT
    print(f"beam_search_plan_v114_32gb_contract_smoke_test ok plan_sha256={sha256_file(V114_LOWMEM_32GB_PLAN_PATH)}")


if __name__ == "__main__":
    main()
