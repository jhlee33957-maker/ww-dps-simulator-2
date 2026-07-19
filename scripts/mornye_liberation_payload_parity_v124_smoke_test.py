from __future__ import annotations

from v124_timing_test_support import MORNYE_LIBERATION_ID, make_mornye_liberation_sim


def payload_snapshot(sim) -> dict:
    state = sim.state
    mornye = state.character_mechanics_state["mornye"]
    return {
        "damage": state.total_damage,
        "resonance_energy": state.resonance_energy["mornye"],
        "concerto": state.concerto_energy["mornye"],
        "off_tune": state.enemy_off_tune_current,
        "cooldown": state.cooldowns[MORNYE_LIBERATION_ID],
        "high_field_remaining": mornye["high_syntony_field_remaining"],
        "high_field_created_count": mornye["high_syntony_field_created_count"],
        "high_field_source": mornye["high_syntony_field_source_action_id"],
        "healing_schedule": [effect.model_dump(mode="json") for effect in state.scheduled_effects],
    }


def run(observation_active: bool, *, stage_2a: bool) -> tuple[dict, object]:
    sim = make_mornye_liberation_sim(observation_active)
    if not stage_2a:
        sim.action_timing_contracts.pop(MORNYE_LIBERATION_ID)
    assert sim.execute_action(MORNYE_LIBERATION_ID)
    return payload_snapshot(sim), sim.last_action_result


def main() -> None:
    action = make_mornye_liberation_sim(False).actions[MORNYE_LIBERATION_ID]
    assert action.hits[0].damage_multiplier == 5.2233
    assert action.concerto_energy_gain == 20
    assert action.resonance_energy_cost == 175
    assert action.off_tune_value == 720
    assert action.cooldown == 25
    for observation_active in (False, True):
        legacy, legacy_result = run(observation_active, stage_2a=False)
        stage_2a, stage_2a_result = run(observation_active, stage_2a=True)
        assert stage_2a == legacy
        assert stage_2a_result.normal_damage == legacy_result.normal_damage
        assert stage_2a_result.concerto_gain == legacy_result.concerto_gain == 20
    print("mornye_liberation_payload_parity_v124_smoke_test ok branches=2")


if __name__ == "__main__":
    main()
