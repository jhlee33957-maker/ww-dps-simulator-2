from __future__ import annotations

import copy
import math

from scheduled_effect_test_helpers import make_sim, snapshot_player_side_effect_state


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def test_source_confirmed_positive_gains() -> None:
    sim = make_sim()
    sim.state.resonance_energy["mornye"] = 100.0
    sim.state.concerto_energy["mornye"] = 10.0
    sim.state.character_states["mornye"]["concerto_energy"] = 10.0
    before = snapshot_player_side_effect_state(sim)

    sim.schedule_effect(
        instance_id="test:mornye:target_damage_resources",
        effect_id="test_target_damage_resources",
        source_character_id="mornye",
        source_action_id="test_source",
        payload_action_id="mornye_syntony_field_target_damage",
        activation_combat_time=0.0,
        remaining_duration=1.0,
        tick_interval=0.1,
        time_until_next_tick=0.1,
        max_trigger_count=1,
        scheduled_resource_policy="source_confirmed_positive_gains",
        source_status="test_source_confirmed",
    )
    row = sim.execute_action("mornye_basic_attack") and sim.timeline[-1]
    event = row.scheduled_damage_events[0]

    assert event["payload_action_id"] == "mornye_syntony_field_target_damage"
    assert event["resource_recipient_character_id"] == "mornye"
    assert_close(event["base_resonance_energy_gain"], 2.08, "base RE")
    assert_close(event["energy_regen"], 2.5424, "Mornye Energy Regen")
    assert_close(event["final_resonance_energy_gain"], 5.288192, "final RE")
    assert_close(event["resonance_energy_gained"], 5.288192, "RE gained")
    assert_close(event["resonance_energy_wasted"], 0.0, "RE wasted")
    assert_close(event["concerto_before"], 10.0, "CE before")
    assert_close(event["concerto_energy_gained"], 6.65, "CE gained")
    assert_close(event["concerto_after"], 16.65, "CE after")
    assert_close(event["concerto_energy_wasted"], 0.0, "CE wasted")
    assert event["resource_cost_applied"] is False
    assert event["cooldown_applied"] is False
    assert event["combo_state_changed"] is False
    assert event["ordinary_player_action_side_effects_applied"] is False
    assert sim.state.active_character_id == before["active_character_id"]


def test_default_policy_still_grants_no_resources() -> None:
    sim = make_sim()
    sim.state.resonance_energy["mornye"] = 100.0
    sim.state.concerto_energy["mornye"] = 10.0
    sim.state.character_states["mornye"]["concerto_energy"] = 10.0
    cooldowns_before = copy.deepcopy(sim.state.cooldowns)

    sim.schedule_effect(
        instance_id="test:mornye:default_resources",
        effect_id="test_default_resources",
        source_character_id="mornye",
        source_action_id="test_source",
        payload_action_id="mornye_syntony_field_target_damage",
        activation_combat_time=0.0,
        remaining_duration=1.0,
        tick_interval=0.1,
        time_until_next_tick=0.1,
        max_trigger_count=1,
        source_status="test_default_none",
    )
    row = sim.execute_action("mornye_basic_attack") and sim.timeline[-1]
    event = row.scheduled_damage_events[0]

    assert event["scheduled_resource_policy"] == "none"
    assert_close(event["base_resonance_energy_gain"], 0.0, "default base RE")
    assert_close(event["resonance_energy_gained"], 0.0, "default RE gained")
    assert_close(event["concerto_energy_gained"], 0.0, "default CE gained")
    assert sim.state.cooldowns == cooldowns_before


def main() -> None:
    test_source_confirmed_positive_gains()
    test_default_policy_still_grants_no_resources()
    print("scheduled_source_resource_gain_smoke_test ok")


if __name__ == "__main__":
    main()
