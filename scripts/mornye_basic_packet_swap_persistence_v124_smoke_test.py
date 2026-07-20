from __future__ import annotations

from v124_timing_test_support import make_sim


def assert_swap_trace(action_id: str, control_frame: int, tail_frames: list[int]) -> None:
    sim = make_sim("mornye")
    assert sim.execute_action(action_id)
    source = next(item for item in sim.state.ongoing_action_instances if item.source_action_id == action_id)
    assert sim.execute_action("swap_to_lynae")
    assert sim.timeline[-1].time_start * 60 == control_frame
    packets = [packet for packet in sim.state.scheduled_packet_instances if packet.action_instance_id == source.action_instance_id]
    assert all(not packet.cancelled for packet in packets)
    remaining = max(0.0, source.start_wall_time + max(tail_frames) / 60 - sim.state.current_time)
    sim.advance_timing_runtime(remaining)
    events = [event for event in sim.state.scheduled_packet_event_log if event.get("action_instance_id") == source.action_instance_id and round(event.get("scheduled_wall_time", 0) * 60) in tail_frames]
    assert [round(event["resolved_wall_time"] * 60) for event in events] == tail_frames
    assert all(event["owner_character_id"] == "mornye" and event["source_action_id"] == action_id for event in events)


def main() -> None:
    assert_swap_trace("mornye_basic_stage_2", 49, [57])
    assert_swap_trace("mornye_basic_stage_3", 50, [58, 67, 76])
    print("mornye_basic_packet_swap_persistence_v124_smoke_test ok stage2=57 stage3=58,67,76")


if __name__ == "__main__":
    main()
