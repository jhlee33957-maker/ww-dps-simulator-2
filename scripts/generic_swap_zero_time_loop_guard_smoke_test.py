from __future__ import annotations

from v114_test_support import build


def main() -> None:
    sim = build()
    assert sim.execute_action("swap_to_mornye")
    assert sim.execute_action("swap_to_lynae")
    assert not sim.execute_action("swap_to_aemeath")
    assert not sim.execute_action("swap_to_mornye")
    assert sim.state.active_character_id == "lynae"
    assert sim.state.current_time == sim.state.combat_time == 0.0
    print("generic_swap_zero_time_loop_guard_smoke_test ok")


if __name__ == "__main__":
    main()

