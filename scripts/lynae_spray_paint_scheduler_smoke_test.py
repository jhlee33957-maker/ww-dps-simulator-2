from __future__ import annotations

from lynae_spray_paint_test_helpers import (
    INSTANCE_ID,
    assert_close,
    collect_spray_events,
    execute_visual_impact,
    relative_frames,
)


def main() -> None:
    sim, row, activation_time = execute_visual_impact("tune_rupture")
    assert row.lynae_spray_paint_scheduled is True
    assert row.lynae_spray_paint_schedule_operation in {"created", "replaced"}
    effect = sim.scheduled_effect_by_instance_id(INSTANCE_ID)
    assert effect is not None
    assert effect.payload_event_type == "status_application"
    assert effect.max_trigger_count == 3
    assert effect.metadata["remove_on_max_trigger_count"] is False
    assert_close(effect.remaining_duration, 5.0, "field duration")
    assert_close(effect.time_until_next_tick, 1.0 / 60.0, "first check")

    events = collect_spray_events(sim, activation_time)
    assert relative_frames(events, activation_time) == [1, 121, 241]
    assert sim.scheduled_effect_by_instance_id(INSTANCE_ID) is None
    assert sim.state.character_mechanics_state["lynae"]["spray_paint_window_remaining"] == 0.0
    print("lynae_spray_paint_scheduler_smoke_test ok")


if __name__ == "__main__":
    main()
