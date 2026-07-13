from __future__ import annotations

from scheduled_effect_test_helpers import make_sim


def run_once() -> dict:
    sim = make_sim(initial_active="mornye")
    for instance_id, metadata in (
        ("sched:mornye:field:b", {"label": "b"}),
        ("sched:mornye:field:a", {"label": "a"}),
    ):
        sim.schedule_effect(
            instance_id=instance_id,
            effect_id="same_timestamp_fixture",
            source_character_id="mornye",
            source_action_id="determinism_fixture",
            payload_action_id="mornye_syntony_field_damage",
            remaining_duration=4.0,
            tick_interval=2.0,
            time_until_next_tick=0.5,
            source_status="scheduler_test_fixture",
            metadata=metadata,
        )
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    return {
        "event_order": [event["scheduled_effect_instance_id"] for event in row.scheduled_damage_events],
        "damage": row.scheduled_damage,
        "off_tune": sim.state.enemy_off_tune_current,
        "logs": row.scheduled_damage_events,
        "effects": [effect.model_dump(mode="json") for effect in sim.state.scheduled_effects],
    }


def main() -> None:
    first = run_once()
    for _ in range(5):
        assert run_once() == first
    assert first["event_order"] == ["sched:mornye:field:b", "sched:mornye:field:a"]
    print("scheduled_effect_determinism_smoke_test ok")


if __name__ == "__main__":
    main()
