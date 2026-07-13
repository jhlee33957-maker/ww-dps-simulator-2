from __future__ import annotations

from scheduled_effect_test_helpers import assert_close, make_sim, schedule_mornye_fixture


def scheduled_damage_for(sim) -> float:
    schedule_mornye_fixture(sim, remaining_duration=4.0, tick_interval=2.0, time_until_next_tick=0.05)
    sim.state.active_character_id = "aemeath"
    assert sim.execute_action("aemeath_basic_attack")
    row = sim.timeline[-1]
    assert row.scheduled_damage > 0.0
    assert row.scheduled_damage_events[0]["source_character_id"] == "mornye"
    assert sim.state.active_character_id == "aemeath"
    return row.scheduled_damage


def main() -> None:
    base = scheduled_damage_for(make_sim(initial_active="aemeath"))
    high_mornye_def = scheduled_damage_for(
        make_sim(initial_active="aemeath", stat_overrides={"mornye": {"def.flat": 1000.0}})
    )
    high_aemeath_atk = scheduled_damage_for(
        make_sim(initial_active="aemeath", stat_overrides={"aemeath": {"flat_atk": 100000.0}})
    )
    assert high_mornye_def > base
    assert_close(high_aemeath_atk, base, "Aemeath attack must not affect off-field Mornye payload")
    print("scheduled_effect_source_character_smoke_test ok")


if __name__ == "__main__":
    main()
