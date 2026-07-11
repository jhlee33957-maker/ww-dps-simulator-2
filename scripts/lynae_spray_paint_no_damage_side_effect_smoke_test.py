from __future__ import annotations

from lynae_spray_paint_test_helpers import execute_visual_impact


def main() -> None:
    sim, _row, _activation_time = execute_visual_impact("tune_rupture")
    before_damage = sim.state.total_damage
    before_off_tune = sim.state.enemy_off_tune_current
    before_re = sim.characters["lynae"].resonance_energy
    before_ce = sim.characters["lynae"].concerto_energy

    assert sim.execute_action("short_wait")
    events = sim.timeline[-1].scheduled_status_application_events
    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "scheduled_status_application"
    assert event["damage"] == 0.0
    assert event["normal_damage"] == 0.0
    assert event["off_tune_value"] == 0.0
    assert event["off_tune_gain"] == 0.0
    assert event["resonance_energy_gain"] == 0.0
    assert event["concerto_energy_gain"] == 0.0
    assert event["reward_contribution"] == 0.0
    assert event["resource_cost_applied"] is False
    assert event["cooldown_applied"] is False
    assert event["ordinary_player_action_side_effects_applied"] is False
    assert sim.state.total_damage == before_damage
    assert sim.state.enemy_off_tune_current == before_off_tune
    assert sim.characters["lynae"].resonance_energy == before_re
    assert sim.characters["lynae"].concerto_energy == before_ce
    print("lynae_spray_paint_no_damage_side_effect_smoke_test ok")


if __name__ == "__main__":
    main()
