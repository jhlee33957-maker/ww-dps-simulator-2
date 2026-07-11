from __future__ import annotations

from lynae_spray_paint_test_helpers import INSTANCE_ID, assert_close, execute_visual_impact


def main() -> None:
    sim, _row, _activation_time = execute_visual_impact("tune_rupture")
    effect = sim.scheduled_effect_by_instance_id(INSTANCE_ID)
    assert effect is not None
    before_remaining = effect.remaining_duration
    before_next = effect.time_until_next_tick
    before_window = sim.state.character_mechanics_state["lynae"]["spray_paint_window_remaining"]

    assert sim.execute_action("lynae_resonance_liberation")
    zero_combat_row = sim.timeline[-1]
    assert_close(zero_combat_row.combat_time_end, zero_combat_row.combat_time_start, "zero combat host")
    effect_after = sim.scheduled_effect_by_instance_id(INSTANCE_ID)
    assert effect_after is not None
    assert_close(effect_after.remaining_duration, before_remaining, "duration frozen")
    assert_close(effect_after.time_until_next_tick, before_next, "next tick frozen")
    assert_close(
        sim.state.character_mechanics_state["lynae"]["spray_paint_window_remaining"],
        before_window,
        "window mirror frozen",
    )
    assert zero_combat_row.scheduled_status_application_events == []
    print("lynae_spray_paint_combat_time_smoke_test ok")


if __name__ == "__main__":
    main()
