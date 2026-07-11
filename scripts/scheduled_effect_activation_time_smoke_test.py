from __future__ import annotations

from scheduled_effect_test_helpers import assert_close, make_sim


def schedule_activation(
    sim,
    *,
    instance_id: str = "sched:activation",
    activation: float,
    duration: float = 8.0,
    interval: float = 0.25,
    phase: float = 0.1,
    trigger_on_apply: bool = False,
):
    return sim.schedule_effect(
        instance_id=instance_id,
        effect_id="activation_time_fixture",
        source_character_id="mornye",
        source_action_id="activation_time_source",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=duration,
        tick_interval=interval,
        time_until_next_tick=phase,
        activation_combat_time=activation,
        trigger_on_apply=trigger_on_apply,
        source_status="scheduler_test_fixture",
    )


def test_future_activation_outside_host_interval() -> None:
    sim = make_sim()
    sim.state.combat_time = 10.0
    schedule_activation(sim, activation=15.0, duration=8.0, interval=2.0, phase=1.0)
    before = sim.scheduled_effect_by_instance_id("sched:activation").model_dump(mode="json")
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    assert row.combat_time_end < 15.0
    assert row.scheduled_damage_events == []
    after = sim.scheduled_effect_by_instance_id("sched:activation").model_dump(mode="json")
    assert after == before


def test_activation_before_interval_start_progresses_full_host() -> None:
    sim = make_sim()
    sim.state.combat_time = 10.0
    schedule_activation(sim, activation=9.5, duration=8.0, interval=2.0, phase=0.25)
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    assert [round(event["combat_time"], 10) for event in row.scheduled_damage_events] == [10.25]
    effect = sim.scheduled_effect_by_instance_id("sched:activation")
    assert_close(effect.remaining_duration, 7.5, "full host duration")
    assert_close(effect.time_until_next_tick, 1.75, "full host phase")


def test_mid_action_activation_without_trigger_on_apply() -> None:
    sim = make_sim()
    sim.state.combat_time = 10.0
    schedule_activation(sim, activation=10.25, duration=8.0, interval=0.25, phase=0.1)
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    assert_close(row.combat_time_start, 10.0, "host start")
    assert_close(row.combat_time_end, 10.5, "host end")
    assert [round(event["combat_time"], 10) for event in row.scheduled_damage_events] == [10.35]
    event = row.scheduled_damage_events[0]
    assert event["scheduled_effect_trigger_kind"] == "periodic"
    effect = sim.scheduled_effect_by_instance_id("sched:activation")
    assert_close(effect.remaining_duration, 7.75, "duration active portion")
    assert_close(effect.time_until_next_tick, 0.1, "next phase from activation")


def test_mid_action_activation_with_trigger_on_apply() -> None:
    sim = make_sim()
    sim.state.combat_time = 10.0
    schedule_activation(
        sim,
        activation=10.25,
        duration=8.0,
        interval=0.125,
        phase=0.125,
        trigger_on_apply=True,
    )
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    events = row.scheduled_damage_events
    assert [event["scheduled_effect_trigger_kind"] for event in events] == [
        "trigger_on_apply",
        "periodic",
        "periodic",
    ]
    assert [round(event["combat_time"], 10) for event in events] == [10.25, 10.375, 10.5]
    assert [event["trigger_index"] for event in events] == [1, 2, 3]
    assert_close(sum(event["off_tune_gain"] for event in events), 66.4 * 3, "off tune once per event")
    effect = sim.scheduled_effect_by_instance_id("sched:activation")
    assert effect.trigger_on_apply_pending is False
    assert effect.trigger_count == 3
    assert_close(effect.remaining_duration, 7.75, "duration active portion")
    assert_close(effect.time_until_next_tick, 0.125, "phase after activation")


def test_zero_combat_time_does_not_reach_future_activation() -> None:
    sim = make_sim(initial_active="aemeath")
    schedule_activation(sim, activation=0.1, duration=8.0, interval=2.0, phase=1.0, trigger_on_apply=True)
    for _ in range(2):
        sim.state.active_character_id = "aemeath"
        sim.state.enemy_tune_break_available = True
        sim.state.enemy_tune_break_cooldown_remaining = 0.0
        assert sim.execute_action("aemeath_tune_break")
        row = sim.timeline[-1]
        assert row.action_time > 0.0
        assert_close(row.effective_combat_time_cost, 0.0, "zero combat host")
        assert row.scheduled_damage_events == []
    effect = sim.scheduled_effect_by_instance_id("sched:activation")
    assert effect.trigger_on_apply_pending is True
    assert effect.trigger_count == 0
    assert_close(effect.remaining_duration, 8.0, "pending duration")
    assert_close(effect.time_until_next_tick, 2.0, "pending phase")

    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    assert [round(event["combat_time"], 10) for event in row.scheduled_damage_events] == [0.1]
    assert row.scheduled_damage_events[0]["scheduled_effect_trigger_kind"] == "trigger_on_apply"


def test_duration_starts_at_activation() -> None:
    sim = make_sim()
    sim.state.combat_time = 20.0
    schedule_activation(sim, activation=20.25, duration=8.0, interval=10.0, phase=10.0)
    assert sim.execute_action("short_wait")
    effect = sim.scheduled_effect_by_instance_id("sched:activation")
    assert_close(effect.remaining_duration, 7.75, "duration reduced only after activation")


def test_exact_activation_expiration_boundary() -> None:
    sim = make_sim()
    sim.state.combat_time = 10.0
    schedule_activation(sim, activation=10.25, duration=0.25, interval=0.25, phase=0.25)
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    assert [round(event["combat_time"], 10) for event in row.scheduled_damage_events] == [10.5]
    assert sim.scheduled_effect_by_instance_id("sched:activation") is None
    assert sim.execute_action("short_wait")
    assert sim.timeline[-1].scheduled_damage_events == []


def main() -> None:
    test_future_activation_outside_host_interval()
    test_activation_before_interval_start_progresses_full_host()
    test_mid_action_activation_without_trigger_on_apply()
    test_mid_action_activation_with_trigger_on_apply()
    test_zero_combat_time_does_not_reach_future_activation()
    test_duration_starts_at_activation()
    test_exact_activation_expiration_boundary()
    print("scheduled_effect_activation_time_smoke_test ok")


if __name__ == "__main__":
    main()
