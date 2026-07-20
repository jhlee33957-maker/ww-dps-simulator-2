from __future__ import annotations

from v124_timing_test_support import make_sim


def main() -> None:
    sim = make_sim("mornye")
    assert sim.execute_action("mornye_basic_stage_3")
    source = next(item for item in sim.state.ongoing_action_instances if item.source_action_id == "mornye_basic_stage_3")
    pending = [packet for packet in sim.state.scheduled_packet_instances if not packet.resolved]
    assert sim.state.current_time * 60 == 50 and not source.ended
    assert [round(packet.scheduled_wall_time * 60) for packet in pending] == [58, 67, 76]
    assert sim.execute_action("mornye_basic_stage_4")
    assert sim.timeline[-1].time_start * 60 == 50
    tails = [event for event in sim.state.scheduled_packet_event_log if event.get("source_action_id") == source.source_action_id and event.get("scheduled_wall_time", 0) * 60 > 50]
    assert [round(event["resolved_wall_time"] * 60) for event in tails] == [58, 67, 76]
    assert all(event["owner_character_id"] == "mornye" and event["action_instance_id"] == source.action_instance_id for event in tails)
    assert abs(sum(row.damage for row in sim.timeline) - sim.state.total_damage) < 1e-9
    print("mornye_basic_stage3_tail_persistence_v124_smoke_test ok next_start=50 tails=58,67,76")


if __name__ == "__main__":
    main()
