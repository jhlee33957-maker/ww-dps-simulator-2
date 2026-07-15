from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_reporting import comparison_for_completed_route
from search.mcts_search import MCTSSearch
from scripts.mcts_v117_test_utils import plan_and_stage


FORBIDDEN = ("beam_reporting", "beam_search", "manual_120s", "models/", "rl.", "stable_baselines3", "sb3_contrib", "torch")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    for name in ("mcts_plan.py", "mcts_state.py", "mcts_tree.py", "mcts_checkpoint.py", "mcts_search.py"):
        text = (root / "search" / name).read_text(encoding="utf-8").lower()
        for token in FORBIDDEN: assert token not in text, (name, token)
    plan, stage = plan_and_stage(simulations=30, combat_duration=4.0)
    with tempfile.TemporaryDirectory(prefix="mcts-independent-") as tmp:
        a = MCTSSearch(plan=plan, stage=stage, output_root=Path(tmp) / "a", allow_test_output_root=True).run()
        b = MCTSSearch(plan=plan, stage=stage, output_root=Path(tmp) / "b", allow_test_output_root=True).run()
        assert a["logical_result_sha256"] == b["logical_result_sha256"]
        fixture = Path(tmp) / "fixture" / "results/beam_search_v114_completed_v116"; fixture.mkdir(parents=True)
        source = root / "results/beam_search_v114_completed_v116/result_manifest.json"
        (fixture / "result_manifest.json").write_bytes(source.read_bytes())
        route = a["best_completed_route"]
        assert comparison_for_completed_route(route, root=Path(tmp) / "fixture")["status"] == "available"
        moved = fixture / "result_manifest.moved"; (fixture / "result_manifest.json").replace(moved)
        assert comparison_for_completed_route(route, root=Path(tmp) / "fixture")["status"] == "unavailable"
        assert a["logical_result_sha256"] == b["logical_result_sha256"]
    print("mcts_search_independence_smoke_test ok")


if __name__ == "__main__": main()
