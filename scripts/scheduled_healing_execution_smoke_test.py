from __future__ import annotations

from mornye_syntony_field_heal_test_helpers import assert_close, make_sim


def snapshot(sim):
    return {
        "active": sim.state.active_character_id,
        "current_time": sim.state.current_time,
        "combat_time": sim.state.combat_time,
        "mornye_re": sim.characters["mornye"].resonance_energy,
        "mornye_ce": sim.characters["mornye"].concerto_energy,
        "cooldowns": dict(sim.state.cooldowns),
        "weapon_cooldowns": dict(sim.state.weapon_effect_cooldowns),
        "enemy_off_tune": sim.state.enemy_off_tune_current,
        "damage": sim.state.total_damage,
    }


def main() -> None:
    sim = make_sim()
    sim.schedule_effect(
        instance_id="test:scheduled_heal",
        effect_id="test_scheduled_heal",
        source_character_id="mornye",
        source_action_id="test",
        payload_action_id="mornye_syntony_field_heal",
        remaining_duration=1.0,
        tick_interval=1.0,
        time_until_next_tick=1.0,
        payload_event_type="healing",
        source_status="test",
        source_ref="test",
    )
    effect = sim.scheduled_effect_by_instance_id("test:scheduled_heal")
    before = snapshot(sim)
    event = sim.execute_scheduled_effect_event(
        effect=effect,
        host_action_id="manual_heal_probe",
        combat_time=sim.state.combat_time,
        host_action_combat_offset=0.0,
        trigger_index=1,
    )
    after = snapshot(sim)
    assert event["event_type"] == "scheduled_heal"
    assert event["damage"] == 0.0 and event["off_tune_gain"] == 0.0
    assert event["resonance_energy_gain"] == 0.0 and event["concerto_energy_gain"] == 0.0
    assert after["active"] == before["active"]
    assert_close(after["current_time"], before["current_time"], "current time")
    assert_close(after["combat_time"], before["combat_time"], "combat time")
    assert after["mornye_re"] == before["mornye_re"]
    assert after["mornye_ce"] == before["mornye_ce"]
    assert after["cooldowns"] == before["cooldowns"]
    assert after["weapon_cooldowns"] == before["weapon_cooldowns"]
    assert after["enemy_off_tune"] == before["enemy_off_tune"]
    assert after["damage"] == before["damage"]
    assert event["hp_application_mode"] == "diagnostic_no_hp_state"
    assert event["effective_hp_restored"] is None
    print("scheduled_healing_execution_smoke_test ok")


if __name__ == "__main__":
    main()
