from __future__ import annotations

from mornye_syntony_field_heal_test_helpers import execute_to_geopotential, make_sim, scheduled_heals


def main() -> None:
    sim = make_sim()
    before = sim.state.mechanic_event_emitted_counts.get("team_heal", 0)
    heavy = execute_to_geopotential(sim)
    assert sim.state.mechanic_event_emitted_counts.get("team_heal", 0) == before + 1
    heal = heavy.scheduled_healing_events[0]
    assert heal["team_heal_event_emitted"] is True
    assert heal["applied_echo_set_effect_ids"] == ["mornye_halo_of_starry_radiance_5set"]
    assert heal["halo_of_starry_radiance_5set_same_action_application"] is False
    assert heal["halo_of_starry_radiance_5set_application_timing"] is None
    assert sim.summary().mornye_halo_of_starry_radiance_5set_trigger_count >= 1
    assert sim.state.mechanic_event_log[-1]["trigger_id"] == "mornye_syntony_field_scheduled_heal"

    while len(scheduled_heals(sim)) < 2:
        assert sim.execute_action("short_wait")
    assert scheduled_heals(sim)[-1]["echo_set_buff_refreshed"] is True
    print("mornye_syntony_field_heal_halo_smoke_test ok")


if __name__ == "__main__":
    main()
