from v124_timing_test_support import make_sim


VIVID = "lynae_to_a_vivid_tomorrow"


def main() -> None:
    sim = make_sim("lynae")
    assert sim.execute_action(VIVID) and sim.state.current_time == 1 / 60
    source = next(item for item in sim.state.ongoing_action_instances if item.source_action_id == VIVID)
    assert sim.execute_action("swap_to_mornye") and source.owner_character_executing
    assert sim.execute_action("mornye_skill_distributed_array")
    assert sim.timeline[-1].time_start == 1 / 60 and not source.ended
    sim.advance_timing_runtime(max(0.0, source.action_end_wall_time - sim.state.current_time))
    events = [event for event in sim.state.scheduled_packet_event_log if event.get("source_action_id") == VIVID and event.get("packet_instance_id")]
    assert len(events) == 22 and all(event["owner_character_id"] == "lynae" for event in events)
    assert [round(event["resolved_wall_time"] * 60) for event in events] == [52, 57, 62, 67, 72, 77, 82, 87, 92, 92, 97, 98, 102, 104, 107, 110, 116, 122, 128, 134, 140, 146]
    assert source.ended and source.action_end_wall_time == 181 / 60
    print("lynae_vivid_immediate_swap_packet_persistence_v124_smoke_test ok 1F_swap packets=22")


if __name__ == "__main__": main()
