from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import V115_RESUME_V114_PLAN_PATH, load_plan
from search.beam_reporting import load_project_comparison_incumbent
from search.beam_search import _leaderboard_payload


def main() -> None:
    plan = load_plan(V115_RESUME_V114_PLAN_PATH)
    stage = plan["stages"][0]
    assert stage["stage_id"] == "full_120s_lowmem_32gb_v114"
    assert stage["result_scope"] == "completed_120s_project_comparison"
    renamed = copy.deepcopy(stage)
    renamed["stage_id"] = "renamed_without_semantic_effect"
    incumbent = load_project_comparison_incumbent(plan)
    result = {"completed_routes": [], "best_partial_frontier_node": {"total_damage": 9999999.0}}
    payload = _leaderboard_payload(result, renamed["stage_id"], result_scope=renamed["result_scope"], incumbent=incumbent)
    assert payload["winner"]["winner_kind"] == "reviewed_v114_model"
    assert payload["partial_nodes_excluded_from_final_winner"] is True
    assert payload["calibration_only_no_project_winner"] is False
    print("beam_search_v114_full_stage_scope_smoke_test ok")


if __name__ == "__main__":
    main()
