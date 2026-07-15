from __future__ import annotations

import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_reporting import replay_completed_route
from search.mcts_search import MCTSSearch
from scripts.mcts_v117_test_utils import plan_and_stage


def main() -> None:
    plan, stage = plan_and_stage(simulations=5, combat_duration=120.0, checkpoint_interval=5)
    with tempfile.TemporaryDirectory(prefix="mcts-replay-") as tmp:
        result = MCTSSearch(plan=plan, stage=stage, output_root=Path(tmp), allow_test_output_root=True).run(); route = result["best_completed_route"]
        assert route is not None; replay = replay_completed_route(route)
        assert replay["final_combat_time"] == 120.0
        assert replay["selected_action_count"] == replay["resolved_action_count"] == replay["executed_action_count"]
        assert all(item["available_before_execution"] and item["executed"] for item in replay["attempted_actions"])
    print("mcts_completed_route_replay_parity_smoke_test ok")


if __name__ == "__main__": main()
