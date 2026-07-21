from __future__ import annotations
import json
from pathlib import Path


def main() -> None:
    progress = json.loads((Path(__file__).resolve().parents[1] / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    current = progress["candidate_history"][-1]
    assert current["candidate"] == "124" and current["stage"] == "timing-core-2d-a2-lynae-outro-concurrent-packets"
    assert current["mornye_heavy_inversion_packet_timing_implemented"] is True
    assert current["distributed_array_complete_first_cast_concerto"] == 51
    assert current["vivid_packet_families_implemented"] is True
    assert current["vivid_measured_1f_swap_persistence_implemented"] is True
    assert current["vivid_off_field_resource_credit_implemented"] is True
    assert current["vivid_source_attribution_implemented"] is True
    assert current["vivid_legacy_aggregate_removed"] is True
    assert current["scheduled_packet_equal_timestamp_numeric_ordering"] is True
    assert current["vivid_92f_source_order_invariant_to_prior_packet_history"] is True
    assert current["vivid_row_2697_persistence"] == "measured pre-179 branch only"
    assert current["lynae_outro_concurrent_packets"] is True
    assert current["lynae_outro_transition_action_time_frames"] == 0
    assert current["lynae_outro_source_lifecycle_frames"] == 181
    assert current["lynae_outro_packet_families_implemented"] is True
    assert current["lynae_outro_raw_multiplier_total"] == 1.001
    assert current["lynae_outro_executable_multiplier_total"] == 1.0
    assert current["lynae_outro_concurrent_incoming_intro"] is True
    assert current["lynae_outro_source_attribution"] is True
    assert current["lynae_outro_legacy_aggregate_removed"] is True
    assert current["lynae_outro_scheduled_packet_damage_executes"] is True
    assert current["lynae_outro_scheduled_packet_base_coefficient_total"] == 1.0
    assert current["lynae_outro_zero_damage_regression"] is False
    assert current["lynae_outro_source_refs_utf8_exact"] is True
    assert current["training_search_blocked"] is True and current["account_first_cycle_executed"] is False
    print("project_progress_timing_core_stage2c_v124_alignment_smoke_test ok")


if __name__ == "__main__": main()
