from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PLAN_SHA256 = "0306c734347e49460fd7273bce546eed80a2db657e460eb707f5cab961a9e0e6"


def main() -> None:
    state = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = state["status"]
    assert status["latest_verified_baseline_label"] == "110"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-110.zip"
    assert status["current_task_expected_next_archive"] == "111"
    assert status["candidate_expected_next_archive"] == "ww-dps-simulator-2-111.zip"
    assert status["current_task_status"] == "implemented_tests_passed_pending_external_review"

    current = state["current_in_progress_task"]
    assert current["candidate"] == "111"
    assert current["external_review_required"] is True
    assert current["external_verification_claimed"] is False
    assert current["latest_externally_verified_baseline"] == "110"
    assert current["beam_search_long_execution"] is False
    assert current["mcts_execution"] is False
    assert current["calibration_stage_executed"] is False
    assert current["full_search_stage_executed"] is False
    assert current["search_objective"] == "deterministic_120s_total_damage_only"
    assert current["current_best_model"] == "models/maskable_ppo_bc_v105.zip"
    assert current["global_optimum_claimed"] is False
    assert current["route_similarity_objective"] is False
    assert current["manual_route_guidance"] is False
    assert current["bc_ppo_policy_guidance"] is False
    assert current["plan_path"] == "data/beam_search_plan_v111.json"

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
    assert history_111["status"] == "implemented_tests_passed_pending_external_review"
    assert history_111["external_review_status"] == "pending"
    assert history_111["external_verification_claimed"] is False
    assert history_111["latest_externally_verified_baseline"] == "110"
    assert history_111["beam_search_long_execution"] is False
    assert history_111["mcts_execution"] is False
    assert history_111["archive_path"] == "../ww-dps-simulator-2-111.zip"

    assert [item["task"] for item in state["next_planned_tasks"]] == [
        "external review of candidate 111",
        "run the 30-second Beam Search calibration stage",
        "review expansion rate, memory, diversity, and pruning diagnostics",
        "run the 120-second full Beam Search stage only after calibration review",
        "compare the best search route against manual, BC, and all PPO checkpoints",
        "use MCTS only if Beam Search coverage is inadequate or excessively myopic",
    ]
    serialized = json.dumps(state, ensure_ascii=False).lower()
    for forbidden in (
        "candidate 109 is pending",
        "execute the reviewed v109 guarded ppo plan",
        '"current_task_expected_next_archive": "109"',
        '"external_verification_claimed": true, "candidate": "111"',
    ):
        assert forbidden not in serialized, forbidden
    print("project_progress_guarded_ppo_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
