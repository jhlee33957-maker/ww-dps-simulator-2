from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_reviewed_archive"] == "ww-dps-simulator-2-124(3).zip"
    assert status["latest_externally_reviewed_archive_sha256"] == "c341c77e0ee461ab8a2e5b450e2813bf6bc1e7cf6164d8cd8920b0a032f67754"
    assert status["current_candidate"] == "124"
    assert status["current_candidate_stage"] == "timing-core-2a-mornye-liberation"
    assert status["current_task_status"] == "candidate_pending_external_review"

    stage = progress["candidate_124_timing_core_1"]
    assert stage["stage"] == "timing-core-2a-mornye-liberation"
    assert stage["status"] == "candidate_pending_external_review"
    assert stage["stage_2a_externally_verified"] is False
    assert stage["mornye_liberation_state_timing_implemented"] is True
    assert stage["mornye_liberation_timing_frames"] == {
        "normal_hit": 272,
        "normal_same_input": 282,
        "observation_hit": 277,
        "observation_same_input": 296,
        "swap": 300,
        "lifecycle_end": 300,
        "global_time_stop": 300,
    }
    assert stage["remaining_p0_packet_action_corrections"] == "pending"
    assert stage["policy_action_count"] == 25
    assert stage["account_observation_version"] == "slot_account_constellation_single_boss_v6"
    assert stage["account_observation_shape"] == 330
    assert stage["observation_v7_required"] is True
    assert stage["training_allowed_after_timing_patch"] is False
    assert stage["search_allowed_after_timing_patch"] is False
    assert stage["historical_results_status"] == "preserved_but_requires_timing_rebaseline"
    assert stage["historical_result_files_rewritten"] is False
    for field in (
        "account_first_cycle_executed",
        "account_120_second_baseline_executed",
        "bc_executed",
        "ppo_executed",
        "beam_executed",
        "mcts_executed",
    ):
        assert stage[field] is False, field

    history = next(item for item in progress["candidate_history"] if item.get("candidate") == "124")
    assert history["stage"] == "timing-core-2a-mornye-liberation"
    assert history["mornye_liberation_state_timing_implemented"] is True
    assert history["account_first_cycle_executed"] is False
    assert history["account_120_second_baseline_executed"] is False
    assert history["bc_ppo_beam_mcts_executed"] is False
    assert history["external_verification_claimed"] is False
    print("project_progress_timing_core_stage2a_v124_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
