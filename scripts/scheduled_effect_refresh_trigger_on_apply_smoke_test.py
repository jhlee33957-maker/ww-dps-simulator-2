from __future__ import annotations

from scheduled_effect_test_helpers import assert_close, make_sim


def schedule(
    sim,
    *,
    refresh_rule: str = "replace",
    trigger_on_apply: bool = True,
    activation_combat_time: float | None = None,
    duration: float = 4.0,
    interval: float = 0.5,
    metadata: dict | None = None,
):
    return sim.schedule_effect(
        instance_id="sched:refresh:on_apply",
        effect_id="refresh_on_apply_fixture",
        source_character_id="mornye",
        source_action_id="refresh_on_apply_source",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=duration,
        tick_interval=interval,
        time_until_next_tick=interval,
        refresh_rule=refresh_rule,
        trigger_on_apply=trigger_on_apply,
        activation_combat_time=activation_combat_time,
        source_status="scheduler_test_fixture",
        metadata=metadata or {},
    )


def test_refresh_duration_ignores_trigger_on_apply() -> None:
    sim = make_sim()
    result = schedule(sim, metadata={"generation": 1})
    assert result["operation"] == "created"
    assert result["immediate_trigger_executed"] is True
    assert len(sim.state.scheduled_effect_event_log) == 1
    effect = sim.scheduled_effect_by_instance_id("sched:refresh:on_apply")
    assert effect.trigger_count == 1
    before_phase = effect.time_until_next_tick
    before_activation = effect.activation_combat_time

    result = schedule(
        sim,
        refresh_rule="refresh_duration",
        trigger_on_apply=True,
        activation_combat_time=99.0,
        duration=9.0,
        interval=0.1,
        metadata={"generation": 2},
    )
    assert result["operation"] == "refreshed"
    assert result["immediate_trigger_pending"] is False
    assert result["immediate_trigger_executed"] is False
    assert len(sim.state.scheduled_effect_event_log) == 1
    effect = sim.scheduled_effect_by_instance_id("sched:refresh:on_apply")
    assert effect.trigger_count == 1
    assert_close(effect.time_until_next_tick, before_phase, "phase preserved")
    assert_close(effect.activation_combat_time, before_activation, "activation preserved")
    assert_close(effect.remaining_duration, 9.0, "duration refreshed")
    assert effect.metadata == {"generation": 1}

    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    assert len(row.scheduled_damage_events) == 1
    assert row.scheduled_damage_events[0]["scheduled_effect_trigger_kind"] == "periodic"
    assert_close(row.scheduled_damage_events[0]["combat_time"], before_phase, "original phase periodic")
    assert sim.scheduled_effect_by_instance_id("sched:refresh:on_apply").trigger_count == 2


def test_keep_existing_ignores_trigger_on_apply() -> None:
    sim = make_sim()
    schedule(sim, trigger_on_apply=False, metadata={"generation": 1})
    before = sim.scheduled_effect_by_instance_id("sched:refresh:on_apply").model_dump(mode="json")
    log_count = len(sim.state.scheduled_effect_event_log)
    result = schedule(
        sim,
        refresh_rule="keep_existing",
        trigger_on_apply=True,
        activation_combat_time=12.0,
        duration=99.0,
        interval=0.1,
        metadata={"generation": 2},
    )
    assert result["operation"] == "kept_existing"
    assert result["immediate_trigger_pending"] is False
    assert result["immediate_trigger_executed"] is False
    after = sim.scheduled_effect_by_instance_id("sched:refresh:on_apply").model_dump(mode="json")
    assert after == before
    assert len(sim.state.scheduled_effect_event_log) == log_count


def test_replace_may_trigger_once() -> None:
    sim = make_sim()
    schedule(sim, metadata={"generation": 1})
    assert len(sim.state.scheduled_effect_event_log) == 1
    result = schedule(
        sim,
        refresh_rule="replace",
        trigger_on_apply=True,
        activation_combat_time=sim.state.combat_time,
        duration=6.0,
        interval=0.25,
        metadata={"generation": 2},
    )
    assert result["operation"] == "replaced"
    assert result["immediate_trigger_executed"] is True
    assert len(sim.state.scheduled_effect_event_log) == 2
    effect = sim.scheduled_effect_by_instance_id("sched:refresh:on_apply")
    assert effect.trigger_count == 1
    assert effect.metadata == {"generation": 2}
    assert_close(effect.time_until_next_tick, 0.25, "replacement phase")


def main() -> None:
    test_refresh_duration_ignores_trigger_on_apply()
    test_keep_existing_ignores_trigger_on_apply()
    test_replace_may_trigger_once()
    print("scheduled_effect_refresh_trigger_on_apply_smoke_test ok")


if __name__ == "__main__":
    main()
