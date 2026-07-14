from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import search.beam_search as beam_search
from scripts.beam_search_v115_resume_test_utils import build_resume_fixture
from search.beam_performance import performance_accounting


def args_for(plan: Path, output: Path, *, resume: bool) -> argparse.Namespace:
    return argparse.Namespace(
        plan=plan, dry_run_plan=False, execute=True, resume=resume,
        only_stage="full_120s_lowmem_32gb_v114", max_expansions=None,
        output_root=output, smoke_run=False, wall_clock_limit_seconds=None,
        memory_budget_bytes=None,
    )


def main() -> None:
    reviewed = performance_accounting(
        cumulative_expansions=4908270,
        invocation_start_expansions=3000000,
        invocation_elapsed_seconds=7659.986105200136,
        prior_cumulative_elapsed_seconds=8955.554317099974,
    )
    assert reviewed["invocation_expansions"] == 1908270
    assert reviewed["invocation_expansions_per_second"] == 249.12186181441405
    assert reviewed["cumulative_elapsed_seconds"] == 16615.54042230011
    assert reviewed["cumulative_expansions_per_second"] == 295.40236882169023
    assert reviewed["expansions_per_second"] != 640.7674808532514
    fresh = performance_accounting(cumulative_expansions=100, invocation_start_expansions=0, invocation_elapsed_seconds=4.0)
    assert fresh["invocation_expansions_per_second"] == fresh["cumulative_expansions_per_second"] == 25.0
    with tempfile.TemporaryDirectory(prefix="beam-v116-performance-") as temporary:
        fixture = build_resume_fixture(Path(temporary), source_budget=20, final_budget=80)
        original_validate = beam_search.validate_plan
        beam_search.validate_plan = lambda plan, plan_path: {"status": "fixture_ok"}
        try:
            resumed = beam_search.run_search_from_args(args_for(fixture["extension_plan_path"], fixture["output_root"], resume=True))
        finally:
            beam_search.validate_plan = original_validate
        assert resumed["invocation_start_expansions"] == 20
        assert resumed["invocation_expansions"] == resumed["expansions"] - 20
        assert resumed["cumulative_accounting_complete"] is True
        expected = resumed["expansions"] / resumed["cumulative_elapsed_seconds"]
        assert abs(resumed["cumulative_expansions_per_second"] - expected) <= 1e-12
        assert resumed["expansions_per_second"] == resumed["invocation_expansions_per_second"]
    print("beam_search_resume_performance_accounting_smoke_test ok")


if __name__ == "__main__":
    main()
