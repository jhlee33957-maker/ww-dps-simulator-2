from stage2c_timing_test_support import ARRAY_ID, packet_events, ready_heavy_sim


def main() -> None:
    sim = ready_heavy_sim(); sim.state.character_mechanics_state["mornye"]["relative_momentum"] = 0.0; assert sim.execute_action(ARRAY_ID)
    events = packet_events(sim, ARRAY_ID)
    assert [e["packet_group_id"] for e in events] == ["mornye_distributed_array_e2_1", "mornye_distributed_array_e2_2", "mornye_distributed_array_e2_3", "mornye_distributed_array_e2_4"]
    assert [e["event_wall_time"] * 60 for e in events] == [22, 22, 36, 36]
    assert all(e["damage_payload"]["damage_multiplier"] == 0.3977 and e["off_tune_value"] == 20 for e in events)
    assert sum(e["base_resonance_energy_gain"] for e in events) == 18.52
    assert sum(e["concerto_energy_gained"] for e in events) == 10.0
    assert sum(e["relative_momentum_gained"] for e in events) == 60.0
    print("mornye_distributed_array_payload_parity_v124_smoke_test ok total=1.5908 off=80 re=18.52 concerto=10 momentum=60")


if __name__ == "__main__": main()
