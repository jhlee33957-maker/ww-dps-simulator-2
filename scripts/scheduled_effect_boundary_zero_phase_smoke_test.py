from __future__ import annotations

from scheduled_effect_test_helpers import assert_close, make_sim


def schedule_boundary(
    sim,
    *,
    instance_id: str = "sched:boundary",
    activation: float,
    duration: float = 8.0,
    interval: float = 2.0,
    phase: float = 0.0,
    trigger_on_apply: bool = False,
    max_trigger_count: int | None = None,
):
    return sim.schedule_effect(
        instance_id=instance_id,
        effect_id="boundary_zero_phase_fixture",
        source_character_id="mornye",
        source_action_id="boundary_zero_phase_source",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=duration,
        tick_interval=interval,
        time_until_next_tick=phase,
        activation_combat_time=activation,
        trigger_on_apply=trigger_on_apply,
        max_trigger_count=max_trigger_count,
        source_status="scheduler_test_fixture",
    )


def tick_host(sim):
    assert sim.execute_action("short_wait")
    return sim.timeline[-1]


def test_activation_at_host_end_zero_phase() -> None:
    sim = make_sim()
    sim.state.combat_time = 10.0
    schedule_boundary(sim, activation=10.5, interval=2.0, phase=0.0)

    first = tick_host(sim)
    assert [event["scheduled_effect_trigger_kind"] for event in first.scheduled_damage_events] == ["periodic"]
    assert_close(first.scheduled_damage_events[0]["combat_time"], 10.5, "boundary tick time")
    effect = sim.scheduled_effect_by_instance_id("sched:boundary")
    assert effect.trigger_count == 1
    assert_close(effect.remaining_duration, 8.0, "boundary remaining")
    assert_close(effect.time_until_next_tick, 2.0, "boundary next phase")

    second = tick_host(sim)
    assert second.combat_time_start == 10.5
    assert second.combat_time_end < 12.5
    assert second.scheduled_damage_events == []
    assert sim.scheduled_effect_by_instance_id("sched:boundary").trigger_count == 1

    for _ in range(2):
        tick_host(sim)
    next_due = tick_host(sim)
    assert [round(event["combat_time"], 10) for event in next_due.scheduled_damage_events] == [12.5]
    assert sim.scheduled_effect_by_instance_id("sched:boundary").trigger_count == 2


def test_trigger_on_apply_at_host_end_has_no_same_timestamp_periodic() -> None:
    sim = make_sim()
    sim.state.combat_time = 20.0
    schedule_boundary(sim, activation=20.5, interval=1.0, phase=0.0, trigger_on_apply=True)
    first = tick_host(sim)
    assert [event["scheduled_effect_trigger_kind"] for event in first.scheduled_damage_events] == [
        "trigger_on_apply"
    ]
    assert_close(first.scheduled_damage_events[0]["combat_time"], 20.5, "trigger-on-apply boundary")
    effect = sim.scheduled_effect_by_instance_id("sched:boundary")
    assert effect.trigger_count == 1
    assert_close(effect.time_until_next_tick, 1.0, "trigger-on-apply next phase")

    second = tick_host(sim)
    assert second.scheduled_damage_events == []
    third = tick_host(sim)
    assert [event["scheduled_effect_trigger_kind"] for event in third.scheduled_damage_events] == ["periodic"]
    assert_close(third.scheduled_damage_events[0]["combat_time"], 21.5, "next periodic")


def test_replace_lifecycle_at_boundary() -> None:
    sim = make_sim()
    sim.state.combat_time = 30.0
    schedule_boundary(sim, activation=30.0, interval=5.0, phase=5.0)
    replacement = sim.schedule_effect(
        instance_id="sched:boundary",
        effect_id="boundary_zero_phase_fixture_replaced",
        source_character_id="mornye",
        source_action_id="boundary_replacement_source",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=8.0,
        tick_interval=1.0,
        time_until_next_tick=0.0,
        activation_combat_time=30.5,
        trigger_on_apply=True,
        refresh_rule="replace",
        source_status="scheduler_test_fixture",
    )
    assert replacement["operation"] == "replaced"
    first = tick_host(sim)
    assert [event["scheduled_effect_trigger_kind"] for event in first.scheduled_damage_events] == [
        "trigger_on_apply"
    ]
    assert first.scheduled_damage_events[0]["scheduled_effect_id"] == "boundary_zero_phase_fixture_replaced"
    effect = sim.scheduled_effect_by_instance_id("sched:boundary")
    assert effect.trigger_count == 1
    assert_close(effect.time_until_next_tick, 1.0, "replacement next phase")
    assert tick_host(sim).scheduled_damage_events == []


def test_exact_expiration_boundary_no_replay() -> None:
    sim = make_sim()
    sim.state.combat_time = 40.0
    schedule_boundary(sim, activation=40.0, duration=0.5, interval=0.5, phase=0.5)
    first = tick_host(sim)
    assert [round(event["combat_time"], 10) for event in first.scheduled_damage_events] == [40.5]
    assert sim.scheduled_effect_by_instance_id("sched:boundary") is None
    assert tick_host(sim).scheduled_damage_events == []


def test_simultaneous_boundary_events_are_deterministic() -> None:
    def run_once() -> dict:
        sim = make_sim()
        sim.state.combat_time = 50.0
        schedule_boundary(sim, instance_id="sched:future-zero", activation=50.5, interval=2.0, phase=0.0)
        schedule_boundary(
            sim,
            instance_id="sched:future-apply",
            activation=50.5,
            interval=2.0,
            phase=0.0,
            trigger_on_apply=True,
        )
        schedule_boundary(sim, instance_id="sched:active-periodic", activation=50.0, interval=2.0, phase=0.5)
        schedule_boundary(
            sim,
            instance_id="sched:expiration",
            activation=50.0,
            duration=0.5,
            interval=0.5,
            phase=0.5,
        )
        row = tick_host(sim)
        no_replay = tick_host(sim)
        return {
            "events": [
                (
                    event["scheduled_effect_instance_id"],
                    event["scheduled_effect_trigger_kind"],
                    round(event["combat_time"], 10),
                    event["trigger_index"],
                )
                for event in row.scheduled_damage_events
            ],
            "damage": row.scheduled_damage,
            "off_tune": sim.state.enemy_off_tune_current,
            "final_effects": [effect.model_dump(mode="json") for effect in sim.state.scheduled_effects],
            "following_events": list(no_replay.scheduled_damage_events),
        }

    first = run_once()
    for _ in range(5):
        assert run_once() == first
    assert first["events"] == [
        ("sched:future-zero", "periodic", 50.5, 1),
        ("sched:future-apply", "trigger_on_apply", 50.5, 1),
        ("sched:active-periodic", "periodic", 50.5, 1),
        ("sched:expiration", "periodic", 50.5, 1),
    ]
    assert first["following_events"] == []


def main() -> None:
    test_activation_at_host_end_zero_phase()
    test_trigger_on_apply_at_host_end_has_no_same_timestamp_periodic()
    test_replace_lifecycle_at_boundary()
    test_exact_expiration_boundary_no_replay()
    test_simultaneous_boundary_events_are_deterministic()
    print("scheduled_effect_boundary_zero_phase_smoke_test ok")


if __name__ == "__main__":
    main()
