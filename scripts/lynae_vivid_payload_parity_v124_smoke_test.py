from v124_timing_test_support import make_sim


def close(actual: float, expected: float) -> None:
    assert abs(actual - expected) < 1e-9, (actual, expected)


def main() -> None:
    sim = make_sim("lynae")
    sim.state.resonance_energy["lynae"] = 0.0
    sim.state.concerto_energy["lynae"] = 0.0
    assert sim.execute_action("lynae_to_a_vivid_tomorrow")
    sim.advance_timing_runtime(181 / 60)
    events = [event for event in sim.state.scheduled_packet_event_log if event.get("source_action_id") == "lynae_to_a_vivid_tomorrow" and event.get("packet_instance_id")]
    first = [event for event in events if event["packet_group_id"] == "row_2697_packet_family"]
    second = [event for event in events if event["packet_group_id"] == "row_2698_packet_family"]
    assert len(first) == 12 and len(second) == 10
    assert all(event["damage_payload"]["damage_multiplier"] == 0.0838 and event["off_tune_value"] == 7.14 for event in first)
    assert all(event["damage_payload"]["damage_multiplier"] == 0.1005 and event["off_tune_value"] == 8.56 for event in second)
    close(sum(event["damage_payload"]["damage_multiplier"] for event in first), 1.0056)
    close(sum(event["damage_payload"]["damage_multiplier"] for event in second), 1.005)
    close(sum(event["off_tune_value"] for event in first), 85.68)
    close(sum(event["off_tune_value"] for event in second), 85.6)
    close(sum(event["base_resonance_energy_gain"] for event in events), 5.46)
    close(sum(event["concerto_energy_gained"] for event in events), 19.42)
    close(sim.state.resonance_energy["lynae"], sum(event["final_resonance_energy_gain"] for event in events))
    close(sim.state.concerto_energy["lynae"], 19.42)
    print("lynae_vivid_payload_parity_v124_smoke_test ok damage=2.0106 off=171.28 re=5.46 concerto=19.42")


if __name__ == "__main__": main()
