from v124_timing_test_support import make_sim


def close(actual: float, expected: float) -> None:
    assert abs(actual - expected) < 1e-9, (actual, expected)


def main() -> None:
    sim = make_sim("lynae")
    sim.state.resonance_energy["lynae"] = 0.0
    sim.state.concerto_energy["lynae"] = 0.0
    assert sim.execute_action("lynae_to_a_vivid_tomorrow")
    assert sim.execute_action("swap_to_mornye")
    assert sim.execute_action("mornye_skill_distributed_array")
    sim.advance_timing_runtime(181 / 60)
    vivid = next(row for row in sim.timeline if row.action_id == "lynae_to_a_vivid_tomorrow")
    mornye = sim.timeline[-1]
    assert len(vivid.scheduled_damage_events) == 22 and vivid.direct_action_damage == 0
    assert mornye.actor_character_id == "mornye"
    assert not any(event.get("source_action_id") == vivid.action_id for event in mornye.scheduled_damage_events)
    assert not any(event.get("packet_group_id") == "legacy_aggregate" for event in vivid.scheduled_damage_events)
    events = [event for event in vivid.scheduled_damage_events if event.get("packet_instance_id")]
    assert len(events) == 22 and all(event["resource_recipient_character_id"] == "lynae" for event in events)
    close(sum(event["base_resonance_energy_gain"] for event in events), 5.46)
    close(sim.state.concerto_energy["lynae"], 19.42)
    close(sum(row.damage for row in sim.timeline), sim.state.total_damage)
    print("lynae_vivid_source_attribution_no_duplicate_v124_smoke_test ok lynae_resources=19.42 packets=22")


if __name__ == "__main__": main()
