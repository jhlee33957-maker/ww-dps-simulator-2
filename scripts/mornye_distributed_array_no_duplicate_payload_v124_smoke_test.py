from stage2c_timing_test_support import ARRAY_ID, packet_events, ready_heavy_sim


def main() -> None:
    sim = ready_heavy_sim(); sim.state.character_mechanics_state["mornye"]["relative_momentum"] = 0.0
    assert sim.execute_action(ARRAY_ID)
    events = packet_events(sim, ARRAY_ID)
    assert len(events) == 4 and sim.last_action_result.direct_action_damage == 0
    assert sum(event["concerto_energy_gained"] for event in events) == 10.0 and sim.state.character_mechanics_state["mornye"]["relative_momentum"] == 60.0
    assert not any(e.get("packet_group_id") == "legacy_aggregate" for e in events)
    print("mornye_distributed_array_no_duplicate_payload_v124_smoke_test ok four_packets_no_aggregate")


if __name__ == "__main__": main()
