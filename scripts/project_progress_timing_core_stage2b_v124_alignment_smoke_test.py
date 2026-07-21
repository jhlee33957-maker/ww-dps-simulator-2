from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_reviewed_archive"] == "ww-dps-simulator-2-124(21).zip"
    assert status["latest_externally_reviewed_archive_sha256"] == "48280980bfe52d5c3e7966f5b87aa9dad996da26c06cedb3c7197d47778ccc41"
    assert status["current_candidate"] == "124"
    assert status["current_candidate_stage"] == "timing-core-2d-b1-lynae-polychrome-leap-stage2"
    stage = progress["candidate_124_timing_core_1"]
    assert stage["stage"] == "timing-core-2d-b1-lynae-polychrome-leap-stage2"
    assert stage["stage_2b_externally_verified"] is False
    for field in (
        "mornye_basic_stage_2_packet_schedule_implemented",
        "mornye_basic_stage_3_packet_schedule_implemented",
        "mornye_basic_detachable_tails_implemented",
        "mornye_basic_legacy_aggregate_duplicate_removed",
        "mornye_basic_payload_parity_preserved",
    ):
        assert stage[field] is True, field
    for field in (
        "scheduled_packet_chronological_interleaving",
        "scheduled_packet_actual_time_processing",
        "scheduled_packet_source_attribution",
        "mornye_tail_before_overlapping_aemeath_hit_verified",
    ):
        assert stage[field] is True, field
    assert stage["scheduled_packet_retroactive_backdating"] is False
    assert stage["candidate_124_smoke_test_count"] == 63
    assert stage["candidate_124_fresh_extraction_command_count"] == 65
    assert stage["authoritative_fresh_extraction_command_count"] == 263
    assert stage["remaining_p0_packet_action_corrections"] == "pending"
    assert stage["policy_action_count"] == 25
    assert stage["account_observation_version"] == "slot_account_constellation_single_boss_v6"
    assert stage["account_observation_shape"] == 330
    assert stage["observation_v7_required"] is True
    assert stage["training_allowed_after_timing_patch"] is False
    assert stage["search_allowed_after_timing_patch"] is False
    for field in ("account_first_cycle_executed", "account_120_second_baseline_executed", "bc_executed", "ppo_executed", "beam_executed", "mcts_executed"):
        assert stage[field] is False, field
    history = next(item for item in progress["candidate_history"] if item.get("candidate") == "124")
    assert history["stage"] == stage["stage"] and history["stage_2b_externally_verified"] is False
    assert history["scheduled_packet_chronological_interleaving"] is True
    assert history["scheduled_packet_actual_time_processing"] is True
    assert history["scheduled_packet_source_attribution"] is True
    assert history["scheduled_packet_retroactive_backdating"] is False
    assert history["mornye_tail_before_overlapping_aemeath_hit_verified"] is True
    assert history["lynae_leap_stage_2_generic_swap_tail_cancellation"] is True
    assert history["bc_ppo_beam_mcts_executed"] is False
    print("project_progress_timing_core_stage2b_v124_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
