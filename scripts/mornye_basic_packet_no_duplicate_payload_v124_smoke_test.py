from __future__ import annotations

from v124_timing_test_support import make_sim


CASES = {
    "mornye_basic_stage_2": (6, 43.0, 19 / 60),
    "mornye_basic_stage_3": (7, 37.0, 41 / 60),
}


def main() -> None:
    for action_id, (packet_count, rest_mass, tail_advance) in CASES.items():
        sim = make_sim("mornye")
        assert sim.execute_action(action_id)
        result = sim.last_action_result
        assert result.direct_action_damage == 0.0 and result.hit_count == 0
        sim.advance_timing_runtime(tail_advance)
        events = [event for event in sim.state.scheduled_packet_event_log if event.get("source_action_id") == action_id and event.get("packet_instance_id")]
        starts = [event for event in sim.state.scheduled_packet_event_log if event.get("source_action_id") == action_id and event["event_type"] == "v124_action_start_payload"]
        assert len(events) == packet_count == len({event["packet_instance_id"] for event in events})
        assert all(event["ordinary_player_action_side_effects_applied"] is False for event in events)
        assert len(starts) == 1 and starts[0]["rest_mass_payload"] == rest_mass
        assert sim.state.character_mechanics_state["mornye"]["rest_mass_energy"] == rest_mass
        assert not any(event["stage_2_payload_resolution_required"] for event in events)
    print("mornye_basic_packet_no_duplicate_payload_v124_smoke_test ok aggregate=0 packets_once rest_once")


if __name__ == "__main__":
    main()
