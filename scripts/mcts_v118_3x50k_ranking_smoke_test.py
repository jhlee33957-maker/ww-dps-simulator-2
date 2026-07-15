from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    compact = root / "results/mcts_v118_production_3x50k_v119"
    leaderboard = json.loads((compact / "seed_leaderboard.json").read_text(encoding="utf-8"))
    assert [row["seed"] for row in leaderboard["ranking"]] == [118003, 118002, 118001]
    comparison = json.loads((compact / "comparison.json").read_text(encoding="utf-8"))
    mcts = [row for row in comparison["candidates"] if row["kind"].startswith("mcts_seed_")]
    beam = next(row for row in comparison["candidates"] if row["kind"] == "beam")
    model = next(row for row in comparison["candidates"] if row["kind"] == "best_trained_model")
    assert all(beam["total_damage"] > row["total_damage"] for row in mcts)
    assert all(model["total_damage"] > row["total_damage"] for row in mcts)
    print("mcts_v118_3x50k_ranking_smoke_test ok 118003>118002>118001 beam/model>all_mcts")


if __name__ == "__main__": main()
