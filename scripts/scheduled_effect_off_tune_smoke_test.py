from __future__ import annotations

from scheduled_effect_test_helpers import assert_close, make_sim, schedule_mornye_fixture


BASE_OFF_TUNE = 66.4


def test_one_and_two_ticks_add_once_per_tick() -> None:
    sim = make_sim()
    schedule_mornye_fixture(
        sim,
        payload_action_id="mornye_syntony_field_target_damage",
        remaining_duration=8.0,
        tick_interval=0.5,
        time_until_next_tick=0.1,
    )
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    assert len(row.scheduled_damage_events) == 1
    assert_close(row.scheduled_damage_events[0]["off_tune_gain"], BASE_OFF_TUNE, "one tick off tune")
    assert_close(sim.state.enemy_off_tune_current, BASE_OFF_TUNE, "one tick gauge")
    assert sim.execute_action("short_wait")
    assert len(sim.timeline[-1].scheduled_damage_events) == 1
    assert_close(sim.state.enemy_off_tune_current, BASE_OFF_TUNE * 2, "two tick gauge")


def test_reaccumulation_lockout_blocks_gain() -> None:
    sim = make_sim()
    sim.state.enemy_tune_break_cooldown_remaining = 1.0
    schedule_mornye_fixture(
        sim,
        payload_action_id="mornye_syntony_field_target_damage",
        remaining_duration=8.0,
        tick_interval=0.5,
        time_until_next_tick=0.1,
    )
    assert sim.execute_action("short_wait")
    event = sim.timeline[-1].scheduled_damage_events[0]
    assert_close(event["off_tune_gain"], 0.0, "blocked gain")
    assert event["off_tune_accumulation_log"]["behavior"] == "blocked_by_tune_break_cooldown"
    assert_close(sim.state.enemy_off_tune_current, 0.0, "blocked gauge")


def test_reaching_max_does_not_execute_tune_break() -> None:
    sim = make_sim()
    sim.state.enemy_off_tune_max = 100.0
    sim.state.enemy_off_tune_current = 90.0
    schedule_mornye_fixture(
        sim,
        payload_action_id="mornye_syntony_field_target_damage",
        remaining_duration=8.0,
        tick_interval=0.5,
        time_until_next_tick=0.1,
    )
    assert sim.execute_action("short_wait")
    assert_close(sim.state.enemy_off_tune_current, 100.0, "capped gauge")
    assert sim.state.enemy_tune_break_available is True
    assert sim.state.enemy_mistune_active is True
    assert sim.state.tune_break_action_used_count == 0
    assert all(log.get("action_type") != "tune_break" for log in sim.state.action_log)


def main() -> None:
    test_one_and_two_ticks_add_once_per_tick()
    test_reaccumulation_lockout_blocks_gain()
    test_reaching_max_does_not_execute_tune_break()
    print("scheduled_effect_off_tune_smoke_test ok")


if __name__ == "__main__":
    main()
