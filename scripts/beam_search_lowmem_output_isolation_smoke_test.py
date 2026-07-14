from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from search.beam_plan import LOWMEM_32GB_PLAN_PATH, ROOT
from search.beam_search import run_search_from_args


def main() -> int:
    args = argparse.Namespace(
        plan=LOWMEM_32GB_PLAN_PATH,
        dry_run_plan=False,
        execute=True,
        resume=True,
        only_stage="full_120s_lowmem_32gb",
        max_expansions=1,
        output_root=ROOT / "results/beam_search_v111_full_120s",
        smoke_run=False,
        wall_clock_limit_seconds=None,
        memory_budget_bytes=None,
    )
    try:
        run_search_from_args(args)
    except ValueError as error:
        assert "abandoned 64 GB" in str(error)
    else:
        raise AssertionError("Low-memory plan accepted old 64GB output root")
    print("beam_search_lowmem_output_isolation_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
