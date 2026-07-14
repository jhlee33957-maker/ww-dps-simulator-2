from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_completed_result import MODEL_DAMAGE, WINNER_DAMAGE, WINNER_ROUTE_ID
from search.beam_reporting import load_overall_project_winner, select_damage_only_winner


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    winner = load_overall_project_winner(root=root)
    assert winner["winner_kind"] == "beam_search_route"
    assert winner["route_id"] == WINNER_ROUTE_ID
    assert winner["total_damage"] == WINNER_DAMAGE > MODEL_DAMAGE
    incumbent = {"winner_kind": "model", "total_damage": MODEL_DAMAGE, "declared_order": 0, "reviewed_project_incumbent": True}
    candidates = [
        {"winner_kind": "partial", "total_damage": WINNER_DAMAGE + 1, "declared_order": 1},
        {"winner_kind": "incomplete", "total_damage": WINNER_DAMAGE + 2, "declared_order": 2},
        {"winner_kind": "beam_search_route", "total_damage": WINNER_DAMAGE, "declared_order": 3},
    ]
    eligible = [item for item in candidates if item["winner_kind"] == "beam_search_route"]
    assert select_damage_only_winner(eligible, incumbent=incumbent)["winner_kind"] == "beam_search_route"
    historical = {"winner_kind": "historical_bc", "total_damage": 5165134.682363356, "declared_order": 0}
    assert select_damage_only_winner([], incumbent=incumbent)["total_damage"] != historical["total_damage"]
    tied = [
        {"winner_kind": "route_later", "total_damage": MODEL_DAMAGE, "declared_order": 2},
        {"winner_kind": "route_earlier", "total_damage": MODEL_DAMAGE, "declared_order": 1},
    ]
    assert select_damage_only_winner(tied, incumbent={"winner_kind": "base", "total_damage": 0.0, "declared_order": 0})["winner_kind"] == "route_earlier"
    print("beam_search_v116_current_winner_smoke_test ok")


if __name__ == "__main__":
    main()
