from __future__ import annotations

from mornye_syntony_field_heal_test_helpers import (
    EXPECTED_HIGH_DEF,
    EXPECTED_HIGH_HEAL,
    EXPECTED_NORMAL_HEAL,
    HIGH_HEAL,
    NORMAL_HEAL,
    assert_close,
    execute_to_geopotential,
    make_sim,
    scheduled_heals,
)


def main() -> None:
    sim = make_sim()
    execute_to_geopotential(sim)
    normal_heals = scheduled_heals(sim)
    assert len(normal_heals) == 1
    assert_close(normal_heals[0]["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "pre-replacement normal heal")

    assert sim.execute_action("mornye_resonance_liberation")
    liberation = sim.timeline[-1]
    assert liberation.combat_time_cost == 0.0
    assert liberation.scheduled_healing_events == []
    assert sim.scheduled_effect_by_instance_id(NORMAL_HEAL) is None
    high_effect = sim.scheduled_effect_by_instance_id(HIGH_HEAL)
    assert high_effect is not None
    assert high_effect.trigger_count == 0

    assert sim.execute_action("mornye_basic_attack")
    high_heals = [event for event in sim.timeline[-1].scheduled_healing_events if event["payload_action_id"] == "mornye_high_syntony_field_heal"]
    assert len(high_heals) == 1
    assert_close(high_heals[0]["source_runtime_def"], EXPECTED_HIGH_DEF, "high runtime DEF")
    assert_close(high_heals[0]["field_healing_multiplier"], 1.4, "high multiplier")
    assert_close(high_heals[0]["calculated_heal_amount"], EXPECTED_HIGH_HEAL, "high heal")
    assert high_heals[0]["healing_bonus_applied"] == 0.0
    print("mornye_high_syntony_field_heal_scheduler_smoke_test ok")


if __name__ == "__main__":
    main()
