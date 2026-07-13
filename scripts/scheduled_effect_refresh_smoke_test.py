from __future__ import annotations

from scheduled_effect_test_helpers import assert_close, make_sim, schedule_mornye_fixture


def test_replace_rule() -> None:
    sim = make_sim()
    schedule_mornye_fixture(sim, remaining_duration=8.0, tick_interval=2.0, time_until_next_tick=1.0, metadata={"old": True})
    effect = sim.scheduled_effect_by_instance_id("sched:mornye:field")
    effect.trigger_count = 3
    result = schedule_mornye_fixture(
        sim,
        remaining_duration=5.0,
        tick_interval=1.5,
        time_until_next_tick=0.25,
        refresh_rule="replace",
        metadata={"new": True},
    )
    assert result["status"] == "replaced"
    effect = sim.scheduled_effect_by_instance_id("sched:mornye:field")
    assert_close(effect.remaining_duration, 5.0, "replace duration")
    assert_close(effect.tick_interval, 1.5, "replace interval")
    assert_close(effect.time_until_next_tick, 0.25, "replace phase")
    assert effect.trigger_count == 0
    assert effect.metadata == {"new": True}


def test_refresh_duration_rule() -> None:
    sim = make_sim()
    schedule_mornye_fixture(sim, remaining_duration=8.0, tick_interval=2.0, time_until_next_tick=0.75, metadata={"old": True})
    effect = sim.scheduled_effect_by_instance_id("sched:mornye:field")
    effect.trigger_count = 2
    result = schedule_mornye_fixture(
        sim,
        remaining_duration=12.0,
        tick_interval=4.0,
        time_until_next_tick=0.1,
        refresh_rule="refresh_duration",
        metadata={"new": True},
    )
    assert result["status"] == "refreshed"
    effect = sim.scheduled_effect_by_instance_id("sched:mornye:field")
    assert_close(effect.remaining_duration, 12.0, "refresh duration")
    assert_close(effect.tick_interval, 2.0, "refresh preserves interval")
    assert_close(effect.time_until_next_tick, 0.75, "refresh preserves phase")
    assert effect.trigger_count == 2
    assert effect.metadata == {"old": True}
    sim.state.active_character_id = "mornye"
    assert sim.execute_action("mornye_basic_attack")
    assert sim.timeline[-1].scheduled_damage_events == []


def test_keep_existing_rule() -> None:
    sim = make_sim()
    schedule_mornye_fixture(sim, remaining_duration=8.0, tick_interval=2.0, time_until_next_tick=1.0, metadata={"old": True})
    before = sim.scheduled_effect_by_instance_id("sched:mornye:field").model_dump(mode="json")
    result = schedule_mornye_fixture(
        sim,
        remaining_duration=3.0,
        tick_interval=0.5,
        time_until_next_tick=0.0,
        refresh_rule="keep_existing",
        metadata={"new": True},
    )
    assert result["status"] == "retained"
    after = sim.scheduled_effect_by_instance_id("sched:mornye:field").model_dump(mode="json")
    assert after == before


def main() -> None:
    test_replace_rule()
    test_refresh_duration_rule()
    test_keep_existing_rule()
    print("scheduled_effect_refresh_smoke_test ok")


if __name__ == "__main__":
    main()
