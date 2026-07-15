from __future__ import annotations

import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_plan import HARD_MEMORY_BUDGET, lowered_memory_budget
from search.mcts_search import MCTSSearch
from scripts.mcts_v117_test_utils import plan_and_stage


def main() -> None:
    try: lowered_memory_budget(HARD_MEMORY_BUDGET, HARD_MEMORY_BUDGET + 1)
    except ValueError: pass
    else: raise AssertionError("CLI raised 22 GiB hard limit")
    plan, stage = plan_and_stage(simulations=10, combat_duration=4.0, checkpoint_interval=5, limit_interval=1)
    stage["memory_budget_bytes"] = 1
    with tempfile.TemporaryDirectory(prefix="mcts-memory-") as tmp:
        output = Path(tmp); first = MCTSSearch(plan=plan, stage=stage, output_root=output, allow_test_output_root=True).run()
        assert first["termination_status"] == "memory_budget_exhausted" and first["simulations_completed"] == 1
        assert (output / "checkpoint/latest_manifest.json").is_file()
        resumed = MCTSSearch(plan=plan, stage=stage, output_root=output, allow_test_output_root=True).run(resume=True)
        assert resumed["termination_status"] == "memory_budget_exhausted" and resumed["simulations_completed"] == 2
        assert stage.get("page_file_assumed", False) is False
    print("mcts_memory_budget_guard_smoke_test ok")


if __name__ == "__main__": main()
