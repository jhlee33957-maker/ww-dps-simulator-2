from __future__ import annotations

from v124_timing_test_support import make_sim


def main() -> None:
    sim = make_sim("mornye")
    assert sim.execute_action("mornye_basic_stage_2")
    source = next(item for item in sim.state.ongoing_action_instances if item.source_action_id == "mornye_basic_stage_2")
    pending = [packet for packet in sim.state.scheduled_packet_instances if not packet.resolved]
    assert sim.state.current_time * 60 == 49
    assert not source.ended and [round(packet.scheduled_wall_time * 60) for packet in pending] == [57]
    assert sim.execute_action("mornye_basic_stage_3")
    assert sim.timeline[-1].time_start * 60 == 49
    tail = next(event for event in sim.state.scheduled_packet_event_log if event.get("scheduled_wall_time") == 57 / 60)
    assert tail["resolved_wall_time"] * 60 == 57
    assert tail["owner_character_id"] == "mornye" and tail["source_action_id"] == "mornye_basic_stage_2"
    assert tail["action_instance_id"] == source.action_instance_id
    assert abs(sum(row.damage for row in sim.timeline) - sim.state.total_damage) < 1e-9
    print("mornye_basic_stage2_tail_persistence_v124_smoke_test ok next_start=49 tail=57")


if __name__ == "__main__":
    main()
