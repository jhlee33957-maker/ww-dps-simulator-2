from __future__ import annotations

from v114_test_support import assert_close, build, set_concerto


def main() -> None:
    sim = build()
    set_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_lynae")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "transition:lynae_intro_time_to_show_some_colors"
    assert_close(row.action_time, 4.0 / 3.0)
    assert row.outgoing_swap_reentry_after_set == 1.0
    assert_close(row.outgoing_swap_reentry_after_action, 0.0)
    assert "swap_reentry:aemeath" not in sim.state.cooldowns
    assert "swap_reentry:lynae" not in sim.state.cooldowns
    assert sim.is_action_available(sim.actions["swap_to_aemeath"])
    print("generic_swap_timed_intro_reentry_cooldown_smoke_test ok")


if __name__ == "__main__":
    main()

