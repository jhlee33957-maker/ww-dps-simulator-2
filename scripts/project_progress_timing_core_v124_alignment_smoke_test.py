from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "123"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-123(3).zip"
    assert status["latest_verified_archive_sha256"] == "2d6c396df09645c4a304acebffea88d41555a6de05ed41d6ee7867648a5712f8"
    assert status["current_candidate"] == "124"
    assert status["current_task"] == "candidate-124 timing-core-1"
    assert status["current_task_status"] == "candidate_pending_external_review"
    assert status["current_task_expected_next_archive"] == "ww-dps-simulator-2-124.zip"
    assert status["candidate_expected_next_archive"] == "ww-dps-simulator-2-124.zip"

    stage = progress["candidate_124_timing_core_1"]
    assert stage["status"] == "candidate_pending_external_review"
    assert stage["stage"] == "timing-core-1"
    assert stage["timing_contract_layer_created"] is True
    assert stage["ongoing_action_instances_created"] is True
    assert stage["scheduled_packet_architecture_created"] is True
    assert stage["swap_reentry_clock_old"] == "combat_time"
    assert stage["swap_reentry_clock"] == "current_time"
    assert stage["vivid_timing_frames"] == {"swap": 1, "same_input": 153, "end": 181, "persistence_cutoff": 179}
    assert stage["lynae_liberation_timing_frames"] == {
        "same_input": 238,
        "swap": 240,
        "end": 299,
        "global_time_stop": 240,
    }
    assert stage["benchmark_observation_version"] == "slot_generic_mechanics_v5"
    assert stage["benchmark_observation_shape"] == 314
    assert stage["account_observation_version"] == "slot_account_constellation_single_boss_v6"
    assert stage["account_observation_shape"] == 330
    assert stage["account_observation_modified_in_stage_1"] is False
    assert stage["markov_state_observation_audit_completed"] is True
    assert stage["observation_v7_required"] is True
    assert stage["training_allowed_after_timing_patch"] is False
    assert stage["search_allowed_after_timing_patch"] is False
    assert stage["policy_action_count"] == 25
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
    assert stage["candidate_124_zip_created"] is True
    assert stage["review_archive_created"] is True
    assert stage["review_archive_name"] == "ww-dps-simulator-2-124.zip"
    assert stage["review_archive_pending_external_review"] is True

    history = next(item for item in progress["candidate_history"] if item.get("candidate") == "124")
    assert history["status"] == "candidate_pending_external_review"
    assert history["external_review_status"] == "pending"
    assert history["external_verification_claimed"] is False
    assert history["candidate_zip_created"] is True
    assert history["review_archive_created"] is True
    assert history["review_archive_name"] == "ww-dps-simulator-2-124.zip"
    assert history["review_archive_pending_external_review"] is True
    print("project_progress_timing_core_v124_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
