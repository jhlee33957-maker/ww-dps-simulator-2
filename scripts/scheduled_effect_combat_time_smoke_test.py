from __future__ import annotations

from scheduled_effect_test_helpers import (
    assert_close,
    execute_aemeath_zero_combat_liberation,
    make_sim,
    schedule_mornye_fixture,
)


def test_zero_combat_time_freezes_scheduler() -> None:
    sim = make_sim(initial_active="aemeath")
    schedule_mornye_fixture(sim, remaining_duration=8.0, tick_interval=2.0, time_until_next_tick=1.0)
    before_current = sim.state.current_time
    before_combat = sim.state.combat_time
    row = execute_aemeath_zero_combat_liberation(sim)
    assert row.action_time > 0.0
    assert_close(row.effective_combat_time_cost, 0.0, "zero combat host")
    assert sim.state.current_time > before_current
    assert_close(sim.state.combat_time, before_combat, "combat time frozen")
    effect = sim.scheduled_effect_by_instance_id("sched:mornye:field")
    assert_close(effect.remaining_duration, 8.0, "remaining frozen")
    assert_close(effect.time_until_next_tick, 1.0, "phase frozen")
    assert effect.trigger_count == 0
    assert_close(row.scheduled_damage, 0.0, "scheduled damage")
    assert row.scheduled_damage_events == []


def test_one_ordinary_tick() -> None:
    sim = make_sim(initial_active="mornye")
    schedule_mornye_fixture(sim, remaining_duration=8.0, tick_interval=2.0, time_until_next_tick=0.25)
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    assert row.effective_combat_time_cost > 0.25
    assert row.effective_combat_time_cost < 2.25
    assert len(row.scheduled_damage_events) == 1
    event = row.scheduled_damage_events[0]
    assert_close(event["combat_time"], row.combat_time_start + 0.25, "tick timestamp")
    assert_close(event["host_action_combat_offset"], 0.25, "host offset")
    effect = sim.scheduled_effect_by_instance_id("sched:mornye:field")
    assert_close(effect.remaining_duration, 8.0 - row.effective_combat_time_cost, "duration decremented once")
    assert_close(
        effect.time_until_next_tick,
        0.25 - row.effective_combat_time_cost + 2.0,
        "next phase",
    )


def test_several_ticks_in_one_action() -> None:
    sim = make_sim(initial_active="mornye")
    schedule_mornye_fixture(sim, remaining_duration=10.0, tick_interval=0.1, time_until_next_tick=0.05)
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    expected_offsets = [0.05, 0.15, 0.25, 0.35, 0.45]
    assert row.effective_combat_time_cost > expected_offsets[-1]
    assert [round(event["host_action_combat_offset"], 10) for event in row.scheduled_damage_events] == expected_offsets
    assert [event["trigger_index"] for event in row.scheduled_damage_events] == [1, 2, 3, 4, 5]


def test_expiration_boundary() -> None:
    sim = make_sim(initial_active="mornye")
    schedule_mornye_fixture(sim, remaining_duration=4.0, tick_interval=2.0, time_until_next_tick=2.0)
    ticks: list[float] = []
    for _ in range(8):
        assert sim.execute_action("short_wait")
        ticks.extend(event["combat_time"] for event in sim.timeline[-1].scheduled_damage_events)
    assert [round(value, 10) for value in ticks] == [2.0, 4.0]
    assert sim.scheduled_effect_by_instance_id("sched:mornye:field") is None
    assert sim.execute_action("short_wait")
    assert sim.timeline[-1].scheduled_damage_events == []


def main() -> None:
    test_zero_combat_time_freezes_scheduler()
    test_one_ordinary_tick()
    test_several_ticks_in_one_action()
    test_expiration_boundary()
    print("scheduled_effect_combat_time_smoke_test ok")


if __name__ == "__main__":
    main()
