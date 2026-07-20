from stage2c_timing_test_support import HEAVY_ID, packet_events, ready_heavy_sim


def main() -> None:
    sim = ready_heavy_sim(); assert sim.execute_action(HEAVY_ID)
    event, = packet_events(sim, HEAVY_ID)
    assert event["damage_payload"]["damage_multiplier"] == 2.5846 and event["off_tune_value"] == 104.0
    assert event["base_resonance_energy_gain"] == 3.25 and event["concerto_energy_gained"] == 11.96
    starts = [e for e in sim.state.scheduled_packet_event_log if e.get("relative_momentum_consumed")]
    assert len(starts) == 1 and starts[0]["relative_momentum_consumed"] == 100
    print("mornye_heavy_inversion_payload_parity_v124_smoke_test ok damage=2.5846 off=104 re=3.25 concerto=11.96")


if __name__ == "__main__": main()
