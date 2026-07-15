from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_state import create_initial_simulation, policy_action_ids
from search.search_state_codec import clone_simulation_for_search, compact_combat_state_payload


def main() -> None:
    states = [create_initial_simulation(combat_duration=120.0)]
    warm = create_initial_simulation(combat_duration=120.0)
    for action in ("aemeath_resonance_liberation", "swap_to_lynae", "lynae_resonance_liberation"):
        if action in warm.valid_action_ids(): warm.execute_action(action)
    states.append(warm)
    checked = 0
    for simulation in states:
        actions = policy_action_ids(simulation)
        for action_id in actions:
            original = clone_simulation_for_search(simulation); clone = clone_simulation_for_search(simulation)
            assert (action_id in original.valid_action_ids()) == (action_id in clone.valid_action_ids())
            if action_id not in original.valid_action_ids(): continue
            assert original.execute_action(action_id) == clone.execute_action(action_id) is True
            assert original.timeline[-1].resolved_action_id == clone.timeline[-1].resolved_action_id
            assert compact_combat_state_payload(original.state, include_objective=True) == compact_combat_state_payload(clone.state, include_objective=True)
            assert clone.state.character_states is clone.state.character_mechanics_state; checked += 1
    assert checked >= 10
    print(f"mcts_state_clone_behavioral_parity_smoke_test ok checked={checked}")


if __name__ == "__main__": main()
