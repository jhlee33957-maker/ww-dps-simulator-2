from __future__ import annotations

from lynae_spray_paint_test_helpers import (
    INSTANCE_ID,
    collect_spray_events,
    execute_visual_impact,
    relative_frames,
    reset_visual_impact_availability,
)


def main() -> None:
    sim, _first_row, _first_activation = execute_visual_impact("tune_rupture")
    assert sim.execute_action("short_wait")
    first_event = sim.timeline[-1].scheduled_status_application_events[0]
    assert first_event["paint_mode_snapshot"] == "tune_rupture"

    reset_visual_impact_availability(sim, "tune_strain")
    assert sim.execute_action("lynae_visual_impact")
    recast_row = sim.timeline[-1]
    recast_activation = float(recast_row.combat_time_end)
    effect = sim.scheduled_effect_by_instance_id(INSTANCE_ID)
    assert effect is not None
    assert effect.trigger_count == 0
    assert effect.metadata["paint_mode_snapshot"] == "tune_strain"
    assert recast_row.lynae_spray_paint_schedule_operation == "replaced"

    events = collect_spray_events(sim, recast_activation)
    assert relative_frames(events, recast_activation) == [1, 121, 241]
    assert {event["paint_mode_snapshot"] for event in events} == {"tune_strain"}
    assert {event["applied_target_shift_state"] for event in events} == {"tune_strain_shifting"}
    print("lynae_spray_paint_recast_smoke_test ok")


if __name__ == "__main__":
    main()
