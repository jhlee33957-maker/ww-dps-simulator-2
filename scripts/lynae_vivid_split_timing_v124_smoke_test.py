from __future__ import annotations

from v124_timing_test_support import VIVID_ID, make_sim
from simulator.action_executor import is_action_valid
from simulator.action_timing_contract import start_ongoing_action


def main() -> None:
    sim = make_sim("lynae")
    action = sim.actions[VIVID_ID]
    assert action.action_time == 149 / 60
    instance = start_ongoing_action(sim.state, action, sim.action_timing_contracts[VIVID_ID])
    assert instance.swap_lock_until_wall_time == 1 / 60
    assert instance.same_character_lock_until_wall_time == 153 / 60
    assert instance.action_end_wall_time == 181 / 60
    sim.advance_timing_runtime(1 / 60)
    assert instance.owner_character_executing and not instance.ended
    assert is_action_valid(sim.actions["swap_to_mornye"], sim.state)[0]
    assert not is_action_valid(sim.actions["lynae_basic_stage_1"], sim.state)[0]
    sim.advance_timing_runtime(151 / 60)
    assert not is_action_valid(sim.actions["lynae_basic_stage_1"], sim.state)[0]
    sim.advance_timing_runtime(1 / 60)
    assert is_action_valid(sim.actions["lynae_basic_stage_1"], sim.state)[0]
    assert not instance.ended
    sim.advance_timing_runtime(28 / 60)
    assert instance.ended
    assert action.action_time == 149 / 60
    print("lynae_vivid_split_timing_v124_smoke_test ok")


if __name__ == "__main__":
    main()
