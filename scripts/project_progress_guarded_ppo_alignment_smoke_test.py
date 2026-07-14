from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PLAN_SHA256 = "0306c734347e49460fd7273bce546eed80a2db657e460eb707f5cab961a9e0e6"


def main() -> None:
    state = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = state["status"]
    assert int(status["latest_verified_baseline_label"]) >= 110

    current = state["current_in_progress_task"]
    assert int(current["candidate"]) >= 111
    assert current["external_review_required"] is True
    assert current["beam_search_long_execution"] is False
    assert current["mcts_execution"] is False
    assert current["full_search_stage_executed"] is False
    assert current["search_objective"] == "deterministic_120s_total_damage_only"
    assert current["current_best_model"] == "models/maskable_ppo_bc_v105.zip"
    assert current["global_optimum_claimed"] is False
    assert current["route_similarity_objective"] is False
    assert current["manual_route_guidance"] is False
    assert current["bc_ppo_policy_guidance"] is False
    assert current["plan_path"] == "data/beam_search_plan_v113_32gb.json"
    assert current["inherited_verified_plan_path"] == "data/beam_search_plan_v111.json"

    history_109 = next(item for item in state["candidate_history"] if item["candidate"] == "109")
    assert history_109["status"] == "externally_verified_complete"
    assert history_109["external_review_status"] == "passed"
    assert history_109["external_verification_claimed"] is True
    assert history_109["baseline_archive"] == "ww-dps-simulator-2(109).zip"
    assert history_109["completed_guarded_checkpoint_count"] == 30
    assert history_109["requested_aggregate_ppo_budget"] == 300000
    assert history_109["actual_aggregate_sb3_model_timesteps"] == 307200
    assert history_109["winner"] == "verified_bc_model"

    history_110 = next(item for item in state["candidate_history"] if item["candidate"] == "110")
    assert history_110["status"] == "externally_verified_complete"
    assert history_110["external_review_status"] == "passed"
    assert history_110["external_verification_claimed"] is True
    assert history_110["latest_externally_verified_baseline"] == "110"
    assert history_110["archive_path"] == "../ww-dps-simulator-2-110.zip"
    assert history_110["completed_guarded_checkpoint_count"] == 30
    assert history_110["requested_aggregate_ppo_budget"] == 300000
    assert history_110["actual_aggregate_sb3_model_timesteps"] == 307200
    assert history_110["winner"] == "verified_bc_model"

    history_111 = next(item for item in state["candidate_history"] if item["candidate"] == "111")
    assert history_111["status"] == "externally_verified_complete"
    assert history_111["external_review_status"] == "passed"
    assert history_111["external_verification_claimed"] is True
    assert history_111["beam_search_long_execution"] is False
    assert history_111["mcts_execution"] is False
    assert history_111["archive_path"] == "../ww-dps-simulator-2-111.zip"

    assert [item["task"] for item in state["next_planned_tasks"]] == [
        "external review of candidate 113",
        "build the slim runtime workspace",
        "run the reviewed 32GB low-memory Beam plan to 3M expansions",
        "review memory, runtime, and best completed 120-second result",
        "resume to 5M only if useful, then run MCTS as an independent complementary search",
    ]
    serialized = json.dumps(state, ensure_ascii=False).lower()
    for forbidden in (
        "candidate 109 is pending",
        "execute the reviewed v109 guarded ppo plan",
        '"current_task_expected_next_archive": "109"',
    ):
        assert forbidden not in serialized, forbidden
    print("project_progress_guarded_ppo_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
