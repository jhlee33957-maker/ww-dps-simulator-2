from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from search.mcts_reporting import replay_completed_route


def main() -> None:
    compact = ROOT / "results/mcts_v117_calibration_20k_v118"
    route = json.loads((compact / "best_route.json").read_text(encoding="utf-8"))["winner"]
    replay = replay_completed_route(route)
    assert replay["selected_action_count"] == replay["resolved_action_count"] == replay["executed_action_count"] == 180
    assert all(item["available_before_execution"] and item["executed"] for item in replay["attempted_actions"])
    assert replay["final_combat_time"] == 120.0 and abs(replay["timeline_damage_sum"] - replay["total_damage"]) < 1e-8
    assert replay["selected_sequence_sha256"] == "5aab329ce5b526a709d530ae0a3037d4e8e776dff7726bfa0ecc4b02ca83116c"
    assert replay["resolved_sequence_sha256"] == "bccd12d7c852d65e168e4ead82fd6fb2514d4d856e865db41a74620699316e1d"
    with (compact / "winning_route_timeline.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    truncated = [row for row in rows if row["truncated_by_combat_limit"].lower() == "true"]
    assert len(truncated) == 1 and truncated[0]["selected_action_id"] == "lynae_visual_impact"
    assert float(truncated[0]["combat_time_start"]) == 119.91666666666664 and float(truncated[0]["damage"]) == 0.0
    print("mcts_v117_20k_winner_replay_parity_smoke_test ok actions=180 damage=4128137.812582737")


if __name__ == "__main__": main()
