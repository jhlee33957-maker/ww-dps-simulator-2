from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import search.beam_search as beam_search
from search.beam_plan import V115_RESUME_V114_PLAN_PATH, load_plan


def args_for(**overrides):
    values = dict(plan=V115_RESUME_V114_PLAN_PATH, dry_run_plan=False, execute=True, resume=True,
                  only_stage="full_120s_lowmem_32gb_v114", max_expansions=6500000, output_root=None,
                  smoke_run=False, wall_clock_limit_seconds=None, memory_budget_bytes=None)
    values.update(overrides)
    return argparse.Namespace(**values)


def expect_failure(args, text: str) -> None:
    try:
        beam_search.run_search_from_args(args)
    except ValueError as error:
        assert text in str(error), error
    else:
        raise AssertionError(text)


def main() -> None:
    plan = load_plan(V115_RESUME_V114_PLAN_PATH)
    renamed = copy.deepcopy(plan); renamed["schema_version"] = "renamed"; renamed["stages"][0]["stage_id"] = "renamed"
    assert beam_search.is_low_memory_execution_plan(plan) is True
    assert beam_search.is_low_memory_execution_plan(renamed) is True
    expect_failure(args_for(memory_budget_bytes=23622320129), "may lower, but may not raise")
    expect_failure(args_for(output_root=ROOT / "results/beam_search_v111_full_120s"), "forbidden legacy")
    expect_failure(args_for(output_root=ROOT / "results/noncanonical_extension"), "exact canonical output root")
    original_load, original_validate = beam_search.load_plan, beam_search.validate_plan
    missing = copy.deepcopy(renamed); missing["stages"][0].pop("memory_budget_bytes")
    beam_search.load_plan = lambda path: missing
    beam_search.validate_plan = lambda plan, plan_path: {"status": "fixture_ok"}
    try:
        expect_failure(args_for(only_stage="renamed", resume=False, output_root=ROOT / "results/noncanonical_fixture"), "requires a hard memory budget")
    finally:
        beam_search.load_plan, beam_search.validate_plan = original_load, original_validate
    assert plan["stages"][0]["memory_budget_bytes"] == 23622320128
    print("beam_search_v115_lowmem_execution_gate_smoke_test ok")


if __name__ == "__main__":
    main()
