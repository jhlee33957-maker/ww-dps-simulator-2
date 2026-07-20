from stage2c_timing_test_support import HEAVY_ID, packet_events, ready_heavy_sim


def main() -> None:
    sim = ready_heavy_sim(); assert sim.execute_action(HEAVY_ID)
    assert len(packet_events(sim, HEAVY_ID)) == 1
    assert sim.last_action_result.direct_action_damage == 0 and sim.last_action_result.scheduled_damage > 0
    assert sim.state.resonance_energy["mornye"] > 0 and sim.state.concerto_energy["mornye"] == 11.96
    print("mornye_heavy_inversion_no_duplicate_payload_v124_smoke_test ok one_packet_no_aggregate")


if __name__ == "__main__": main()
