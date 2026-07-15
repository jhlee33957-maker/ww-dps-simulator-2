from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_production_result import COMPACT_RESULT, SEEDS
from search.mcts_reporting import replay_completed_route


def main() -> None:
    for seed, expected in SEEDS.items():
        seed_dir = ROOT / COMPACT_RESULT / f"seed_{seed}"
        route = json.loads((seed_dir / "best_route.json").read_text(encoding="utf-8"))["winner"]
        replay = replay_completed_route(route)
        assert replay["selected_action_count"] == replay["resolved_action_count"] == replay["executed_action_count"] == expected["actions"]
        assert replay["selected_sequence_sha256"] == expected["selected_sha"]
        assert replay["resolved_sequence_sha256"] == expected["resolved_sha"]
        assert replay["total_damage"] == expected["damage"] and replay["final_combat_time"] == 120.0
    seed_dir = ROOT / COMPACT_RESULT / "seed_118003"
    summary = json.loads((seed_dir / "winning_route_summary.json").read_text(encoding="utf-8"))
    assert summary["selected_action_count"] == summary["resolved_action_count"] == summary["executed_action_count"] == 174
    assert all(row["available_before_execution"] and row["executed"] for row in summary["attempted_actions"])
    assert summary["timeline_damage_sum"] == 4647724.703247971
    assert summary["total_damage"] == 4647724.703247974
    with (seed_dir / "winning_route_timeline.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    truncated = [row for row in rows if row["truncated_by_combat_limit"].lower() == "true"]
    assert len(truncated) == 1 and truncated[0]["resolved_action_id"] == "aemeath_basic_form_stage_2"
    assert float(truncated[0]["damage"]) == 0.0
    print("mcts_v118_3x50k_winner_replay_parity_smoke_test ok winners=3 seed118003_truncation=exact")


if __name__ == "__main__": main()
