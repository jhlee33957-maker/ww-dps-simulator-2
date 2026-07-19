from __future__ import annotations

from v124_timing_test_support import make_sim
from simulator.party_transition import fallback_swap_timing, swap_reentry_key


def main() -> None:
    sim = make_sim("mornye")
    assert fallback_swap_timing(sim.transition_config, sim.preset_generic_swap)["reentry_cooldown_clock"] == "current_time"
    assert sim.execute_action("swap_to_lynae")
    key = swap_reentry_key("mornye")
    assert sim.state.cooldowns[key] == 1.0
    sim.advance_timing_runtime(1.0, combat_elapsed=0.0)
    assert key not in sim.state.cooldowns
    assert sim.state.current_time == 1.0 and sim.state.combat_time == 0.0
    print("swap_reentry_wall_clock_v124_smoke_test ok")


if __name__ == "__main__":
    main()

