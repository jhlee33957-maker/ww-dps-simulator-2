from __future__ import annotations

import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import LOWMEM_32GB_PLAN_PATH, load_plan
from search.beam_search import BeamSearchRunner
from search.beam_state import make_node


class InterruptAfterOneExpansion(BeamSearchRunner):
    def _memory_budget_exceeded(self) -> bool:
        return self.expansions >= 1


def main() -> int:
    plan = load_plan(LOWMEM_32GB_PLAN_PATH)
    stage = dict(plan["stages"][0])
    assert stage["memory_budget_bytes"] == 22 * 1024**3
    assert plan["memory_estimate_contract"]["windows_page_file_assumed"] is False
    missing = dict(stage)
    missing.pop("memory_budget_bytes")
    assert missing.get("memory_budget_bytes") is None
    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "memory-stop"
        first_stage = dict(stage, maximum_expansions=10)
        first = InterruptAfterOneExpansion(plan=plan, stage=first_stage, plan_path=LOWMEM_32GB_PLAN_PATH, output_root=output).run()
        assert first["termination_status"] == "memory_budget_exhausted"
        assert 1 <= first["expansions"] < 10
        resume_stage = dict(stage, maximum_expansions=11)
        resumed = BeamSearchRunner(plan=plan, stage=resume_stage, plan_path=LOWMEM_32GB_PLAN_PATH, output_root=output).run(resume=True)
        assert resumed["expansions"] == 11
        assert resumed["termination_status"] == "expansion_budget_exhausted"
        assert resumed["next_node_id"] > first["next_node_id"]

        cursor_output = Path(temporary) / "cursor-resume"
        cursor_runner = BeamSearchRunner(plan=plan, stage=first_stage, plan_path=LOWMEM_32GB_PLAN_PATH, output_root=cursor_output)
        cursor_runner.frontier_root.mkdir(parents=True)
        cursor_runner.accumulator_root.mkdir(parents=True)
        cursor_runner.logs_root.mkdir(parents=True)
        root_node = make_node(simulation=cursor_runner._create_simulation(), node_id=0)
        cursor_runner.route_store[0] = {"node_id": 0, "parent_id": None, "selected_action_id": None, "resolved_action_id": None}
        cursor_runner._interrupt_retained_queue(
            bucket_index=0,
            retained=[root_node],
            retained_index=0,
            node_id=0,
            next_action_index=1,
            action_count=2,
        )
        cursor_runner._save_manifest(status="memory_budget_exhausted", force=True)
        restored = BeamSearchRunner(plan=plan, stage=first_stage, plan_path=LOWMEM_32GB_PLAN_PATH, output_root=cursor_output)
        restored._load_resume_state()
        assert restored.partial_action_cursors == {0: 1}
        assert restored.bucket_resume_queues == {0: [0]}
    print("beam_search_lowmem_memory_guard_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
