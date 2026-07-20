from __future__ import annotations

from copy import deepcopy

from v124_timing_test_support import LIBERATION_ID, make_sim
from simulator.action_executor import reduce_cooldowns
from simulator.party_transition import default_transition_config, fallback_swap_timing, swap_reentry_key


def main() -> None:
    sim = make_sim("mornye")
    assert default_transition_config()["generic_swap_fallback"]["reentry_cooldown_clock"] == "combat_time"
    assert fallback_swap_timing(sim.transition_config, sim.preset_generic_swap)["reentry_cooldown_clock"] == "combat_time"
    timing_runtime = sim.state.mechanics_config["timing_runtime"]
    assert timing_runtime == {
        "swap_reentry_cooldown_clock": "current_time",
        "swap_reentry_cooldown_clock_source": "candidate_124_timing_runtime_override",
        "historical_swap_reentry_clock": "combat_time",
    }
    assert sim.execute_action("swap_to_lynae")
    key = swap_reentry_key("mornye")
    assert sim.state.cooldowns[key] == 1.0
    sim.state.resonance_energy["lynae"] = 125.0
    assert sim.execute_action(LIBERATION_ID)
    assert key not in sim.state.cooldowns
    assert sim.state.current_time == 238 / 60 and sim.state.combat_time == 0.0

    legacy_state = deepcopy(sim.state)
    legacy_state.mechanics_config.pop("timing_runtime", None)
    legacy_state.cooldowns[key] = 1.0
    reduce_cooldowns(legacy_state, 0.0, action_elapsed=1.0)
    assert legacy_state.cooldowns[key] == 1.0
    reduce_cooldowns(legacy_state, 1.0, action_elapsed=1.0)
    assert key not in legacy_state.cooldowns
    print("swap_reentry_wall_clock_v124_smoke_test ok historical=combat_time effective=current_time")


if __name__ == "__main__":
    main()
