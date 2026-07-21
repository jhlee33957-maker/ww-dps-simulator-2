from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lynae_polychrome_leap_stage2_frame1_resource_timing_v124_smoke_test import ready_stage_2


def main() -> None:
    sim = ready_stage_2()
    assert sim.execute_action("lynae_polychrome_leap")
    stage_2 = sim.timeline[-1]
    instance = next(
        item for item in sim.state.ongoing_action_instances
        if item.source_action_id == "lynae_polychrome_leap_stage_2"
    )
    assert instance.selected_swap_input_frame is None
    assert instance.selected_source_action_end_frame is None
    assert instance.effective_swap_lock_source == "unresolved_swap_same_character_control_fallback"
    assert instance.effective_swap_lock_until_wall_time == stage_2.time_start + 36 / 60
    assert instance.swap_lock_until_wall_time == instance.effective_swap_lock_until_wall_time
    assert instance.lifecycle_end_wall_time == stage_2.time_start + 42 / 60
    assert sim.state.current_time == stage_2.time_start + 36 / 60

    assert sim.execute_action("swap_to_mornye")
    assert sim.state.active_character_id == "mornye"
    assert not instance.owner_character_executing

    damage_packets = [
        packet for packet in sim.state.scheduled_packet_instances
        if packet.action_instance_id == instance.action_instance_id and packet.packet_group_id != "frame_1_true_color_lumiflow"
    ]
    assert len(damage_packets) == 6
    packet_6 = next(packet for packet in damage_packets if packet.packet_occurrence_index == 6)
    assert packet_6.cancelled and not packet_6.resolved
    assert all(packet.resolved and not packet.cancelled for packet in damage_packets if packet.packet_occurrence_index < 6)

    assert sim.execute_action("mornye_basic_attack")
    assert packet_6.cancelled and not packet_6.resolved
    resolved_stage_2_damage = [
        event for event in sim.state.chronological_event_log
        if event.get("source_action_id") == "lynae_polychrome_leap_stage_2"
        and event.get("packet_group_id") in {"tune_rupture_packet_family", "tune_strain_packet_family"}
    ]
    assert len(resolved_stage_2_damage) == 5
    assert {event["packet_occurrence_index"] for event in resolved_stage_2_damage} == {1, 2, 3, 4, 5}
    print("lynae_polychrome_leap_stage2_generic_swap_cancels_tail_v124_smoke_test ok")


if __name__ == "__main__":
    main()
