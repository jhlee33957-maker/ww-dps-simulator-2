from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_reporting import select_damage_only_winner
from search.beam_search import _leaderboard_payload


def main() -> None:
    tie = select_damage_only_winner([{"winner_kind": "search_route", "total_damage": 5165134.682363356, "declared_order": 1, "route_similarity": 0.0}])
    assert tie["winner_kind"] == "verified_bc_model"
    better = select_damage_only_winner([{"winner_kind": "search_route", "total_damage": 5165134.682363356 + 0.01, "declared_order": 1, "route_similarity": 0.0}])
    assert better["winner_kind"] == "search_route"
    assert better["total_damage"] > 5165134.682363356
    equal_runner = _leaderboard_payload(
        {"completed_routes": [{"total_damage": 5165134.682363356}], "best_partial_frontier_node": {"total_damage": 9999999.0}},
        "full_120s",
    )
    assert equal_runner["winner"]["winner_kind"] == "verified_bc_model"
    lower_runner = _leaderboard_payload({"completed_routes": [{"total_damage": 1.0}], "best_partial_frontier_node": {"total_damage": 9999999.0}}, "full_120s")
    assert lower_runner["winner"]["winner_kind"] == "verified_bc_model"
    higher_runner = _leaderboard_payload({"completed_routes": [{"total_damage": 5165134.682365}], "best_partial_frontier_node": {"total_damage": 1.0}}, "full_120s")
    assert higher_runner["winner"]["winner_kind"] == "beam_search_route"
    calibration = _leaderboard_payload({"completed_routes": [{"total_damage": 9999999.0}], "best_partial_frontier_node": None}, "calibration_30s")
    assert calibration["winner"] is None
    print("beam_search_damage_only_winner_smoke_test ok")


if __name__ == "__main__":
    main()
