from __future__ import annotations

from v124_timing_test_support import make_sim
from simulator.action_executor import resolve_action_runtime_timing


def main() -> None:
    sim = make_sim("mornye")
    action = sim.actions["mornye_basic_stage_1"]
    assert action.id not in sim.action_timing_contracts
    assert resolve_action_runtime_timing(action) == (action.duration, action.effective_action_time, action.effective_combat_time_cost)
    before = (sim.state.current_time, sim.state.combat_time)
    assert sim.execute_action("mornye_basic_stage_1")
    assert sim.state.current_time - before[0] == action.effective_action_time
    assert sim.state.combat_time - before[1] == action.effective_combat_time_cost
    print("action_timing_contract_v124_backward_compatibility_smoke_test ok")


if __name__ == "__main__":
    main()

