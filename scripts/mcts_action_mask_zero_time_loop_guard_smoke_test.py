from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_state import create_initial_simulation


def main() -> None:
    simulation = create_initial_simulation(combat_duration=120.0); zero = 0
    for _ in range(64):
        swaps = [action for action in simulation.valid_action_ids() if action.startswith("swap_to_")]
        if not swaps: break
        before = simulation.state.combat_time; assert simulation.execute_action(swaps[0])
        zero = zero + 1 if simulation.state.combat_time <= before + 1e-12 else 0
        assert zero <= 32
        assert f"swap_to_{simulation.timeline[-1].actor_character_id}" not in simulation.valid_action_ids()
        non_swap = next(action for action in simulation.valid_action_ids() if not action.startswith("swap_to_"))
        simulation.execute_action(non_swap)
    assert simulation.state.combat_time > 0.0
    print("mcts_action_mask_zero_time_loop_guard_smoke_test ok")


if __name__ == "__main__": main()
