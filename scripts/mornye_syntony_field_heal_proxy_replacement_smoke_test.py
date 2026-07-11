from __future__ import annotations

from mornye_syntony_field_heal_test_helpers import execute_to_geopotential, make_sim, scheduled_heals


def main() -> None:
    sim = make_sim()
    assert sim.summary().mornye_heal_event_mode == "scheduled_180f_exact"
    start_count = sim.state.mechanic_event_emitted_counts.get("team_heal", 0)
    execute_to_geopotential(sim)
    assert sim.state.mechanic_event_emitted_counts.get("team_heal", 0) == start_count + 1
    for event in sim.state.mechanic_event_log:
        assert "proxy" not in event.get("trigger_id", "")
        assert event.get("event_source") == "scheduled_180f_exact"
    count_after_first = sim.state.mechanic_event_emitted_counts.get("team_heal", 0)
    assert sim.execute_action("mornye_resonance_liberation")
    assert sim.state.mechanic_event_emitted_counts.get("team_heal", 0) == count_after_first
    assert len([event for event in scheduled_heals(sim) if event["payload_action_id"] == "mornye_high_syntony_field_heal"]) == 0
    print("mornye_syntony_field_heal_proxy_replacement_smoke_test ok")


if __name__ == "__main__":
    main()
