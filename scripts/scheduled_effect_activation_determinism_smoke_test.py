from __future__ import annotations

from scheduled_effect_test_helpers import make_sim


def run_once() -> dict:
    sim = make_sim()
    sim.state.combat_time = 10.0
    sim.schedule_effect(
        instance_id="sched:active:periodic",
        effect_id="activation_determinism_fixture",
        source_character_id="mornye",
        source_action_id="activation_determinism",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=8.0,
        tick_interval=1.0,
        time_until_next_tick=0.25,
        activation_combat_time=10.0,
        source_status="scheduler_test_fixture",
        metadata={"order": "periodic"},
    )
    for instance_id in ("sched:future:a", "sched:future:b"):
        sim.schedule_effect(
            instance_id=instance_id,
            effect_id="activation_determinism_fixture",
            source_character_id="mornye",
            source_action_id="activation_determinism",
            payload_action_id="mornye_syntony_field_damage",
            remaining_duration=8.0,
            tick_interval=1.0,
            time_until_next_tick=1.0,
            activation_combat_time=10.25,
            trigger_on_apply=True,
            source_status="scheduler_test_fixture",
            metadata={"order": instance_id},
        )
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    return {
        "event_order": [
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
        "logs": row.scheduled_damage_events,
        "effects": [effect.model_dump(mode="json") for effect in sim.state.scheduled_effects],
    }


def main() -> None:
    first = run_once()
    for _ in range(5):
        assert run_once() == first
    assert first["event_order"] == [
        ("sched:active:periodic", "periodic", 10.25, 1),
        ("sched:future:a", "trigger_on_apply", 10.25, 1),
        ("sched:future:b", "trigger_on_apply", 10.25, 1),
    ]
    print("scheduled_effect_activation_determinism_smoke_test ok")


if __name__ == "__main__":
    main()
