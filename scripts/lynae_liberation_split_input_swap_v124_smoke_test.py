from __future__ import annotations

from v124_timing_test_support import LIBERATION_ID, make_sim
from simulator.action_executor import is_action_valid
from simulator.action_timing_contract import start_ongoing_action


def main() -> None:
    sim = make_sim("lynae")
    start_ongoing_action(sim.state, sim.actions[LIBERATION_ID], sim.action_timing_contracts[LIBERATION_ID])
    followup = sim.actions["lynae_basic_stage_1"]
    swap = sim.actions["swap_to_mornye"]
    sim.advance_timing_runtime(237 / 60, combat_elapsed=0)
    assert not is_action_valid(followup, sim.state)[0]
    assert not is_action_valid(swap, sim.state)[0]
    sim.advance_timing_runtime(1 / 60, combat_elapsed=0)
    assert is_action_valid(followup, sim.state)[0]
    assert not is_action_valid(swap, sim.state)[0]
    sim.advance_timing_runtime(1 / 60, combat_elapsed=0)
    assert not is_action_valid(swap, sim.state)[0]
    sim.advance_timing_runtime(1 / 60, combat_elapsed=0)
    assert is_action_valid(swap, sim.state)[0]
    assert sim.state.current_time == 4.0
    assert sim.state.combat_time == 0.0
    print("lynae_liberation_split_input_swap_v124_smoke_test ok")


if __name__ == "__main__":
    main()

