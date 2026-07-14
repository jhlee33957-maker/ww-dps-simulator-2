from __future__ import annotations

from v114_test_support import add_wait, assert_close, build


def main() -> None:
    sim = build()
    assert sim.execute_action("aemeath_echo_sigillum")
    scheduled_before = [effect.model_dump(mode="json") for effect in sim.state.scheduled_effects]
    sigillum_cooldown_before = sim.state.cooldowns["aemeath_echo_sigillum"]
    scheduled_log_count_before = len(sim.state.scheduled_effect_event_log)
    before_buffs = [(b.buff_id, b.remaining_duration) for b in sim.state.active_buffs]
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    assert row.generic_swap_zero_time
    assert_close(row.action_time, 0.0)
    assert_close(row.combat_time_cost, 0.0)
    assert_close(sim.state.current_time, 0.0)
    assert_close(sim.state.combat_time, 0.0)
    assert_close(sim.state.cooldowns["swap_reentry:aemeath"], 1.0)
    assert "swap_reentry:mornye" not in sim.state.cooldowns
    assert sim.state.cooldowns["aemeath_echo_sigillum"] == sigillum_cooldown_before
    assert [effect.model_dump(mode="json") for effect in sim.state.scheduled_effects] == scheduled_before
    assert len(sim.state.scheduled_effect_event_log) == scheduled_log_count_before
    assert before_buffs == [(b.buff_id, b.remaining_duration) for b in sim.state.active_buffs]
    assert sim.execute_action("swap_to_lynae")
    assert_close(sim.state.cooldowns["swap_reentry:aemeath"], 1.0)
    assert_close(sim.state.cooldowns["swap_reentry:mornye"], 1.0)
    assert not sim.execute_action("swap_to_aemeath")
    assert not sim.execute_action("swap_to_mornye")
    wait = add_wait(sim, 0.5)
    assert sim.execute_action(wait)
    assert_close(sim.state.cooldowns["swap_reentry:aemeath"], 0.5)
    assert_close(sim.state.cooldowns["swap_reentry:mornye"], 0.5)
    assert sim.execute_action(wait)
    assert "swap_reentry:aemeath" not in sim.state.cooldowns
    assert "swap_reentry:mornye" not in sim.state.cooldowns
    assert sim.is_action_available(sim.actions["swap_to_aemeath"])
    assert sim.is_action_available(sim.actions["swap_to_mornye"])
    print("generic_swap_zero_time_reentry_cooldown_smoke_test ok")


if __name__ == "__main__":
    main()
