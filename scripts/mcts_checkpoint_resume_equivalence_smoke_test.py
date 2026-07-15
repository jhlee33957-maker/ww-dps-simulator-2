from __future__ import annotations

import tempfile
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_search import MCTSSearch
from scripts.mcts_v117_test_utils import plan_and_stage


def main() -> None:
    plan, stage = plan_and_stage(simulations=500, combat_duration=4.0, checkpoint_interval=200)
    with tempfile.TemporaryDirectory(prefix="mcts-resume-") as tmp:
        root = Path(tmp); full = MCTSSearch(plan=plan, stage=stage, output_root=root / "full", allow_test_output_root=True).run()
        first = MCTSSearch(plan=plan, stage=stage, output_root=root / "resumed", max_simulations=200, allow_test_output_root=True).run()
        resumed_runner = MCTSSearch(plan=plan, stage=stage, output_root=root / "resumed", max_simulations=500, allow_test_output_root=True)
        resumed = resumed_runner.run(resume=True)
        assert full["logical_result_sha256"] == resumed["logical_result_sha256"]
        assert full["rng_final_state_sha256"] == resumed["rng_final_state_sha256"]
        assert full["mast_logical_sha256"] == resumed["mast_logical_sha256"]
        assert full["completed_rollout_count"] == resumed["completed_rollout_count"]
        assert first["simulations_completed"] == 200 and resumed["simulations_completed"] == 500
    print(f"mcts_checkpoint_resume_equivalence_smoke_test ok logical={full['logical_result_sha256']}")


if __name__ == "__main__": main()
