from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_destination_bucket_test_utils import make_node
from search.beam_plan import LOWMEM_32GB_PLAN_PATH, load_plan
from search.beam_search import BeamSearchRunner


def main() -> int:
    plan = load_plan(LOWMEM_32GB_PLAN_PATH)
    stage = dict(plan["stages"][0], maximum_expansions=10_000)
    nodes = [make_node(index, damage=50_000.0 - index, key=f"key-{index % 400}") for index in range(1, 4202)]
    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "probe"
        runner = BeamSearchRunner(plan=plan, stage=stage, plan_path=LOWMEM_32GB_PLAN_PATH, output_root=output)
        runner.frontier_root.mkdir(parents=True)
        runner.accumulator_root.mkdir(parents=True)
        runner.logs_root.mkdir(parents=True)
        accumulator = runner._new_accumulator(9)
        for node in nodes:
            accumulator.add(node)
        runner.pending_accumulators[9] = accumulator
        runner.pending[9] = []
        runner.dirty_buckets.add(9)

        for _ in range(3):
            runner._save_manifest(status="interrupted_resumable", force=True)
            accumulator.manifest(retained_view_count=0)
            accumulator.cheap_metrics()
            accumulator.to_json()
        metrics = accumulator.cheap_metrics()
        assert metrics["spill_write_count"] == 2
        assert metrics["spill_restore_pass_count"] == 0
        assert metrics["spill_restore_nodes_streamed"] == 0
        assert metrics["full_accumulator_finalization_count"] == 0
        assert metrics["finalization_needed"] is True
        state = json.loads((output / "search_state.json").read_text(encoding="utf-8"))
        saved = state["destination_bucket_accumulators"]["9"]
        assert saved["finalization_needed"] is True
        assert len(saved["spill_chunks"]) == 2
        assert state["destination_bucket_accumulator_metrics"]["9"]["spill_restore_pass_count"] == 0
    print("beam_search_lowmem_spill_no_repeated_rescan_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
