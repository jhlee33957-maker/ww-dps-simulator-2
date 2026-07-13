from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import clone_simulation_for_search, future_state_fingerprint  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    original = _sim()
    original_fp = future_state_fingerprint(original)
    child_a = clone_simulation_for_search(original)
    child_b = clone_simulation_for_search(original)
    assert child_a.state is not original.state
    assert child_b.state is not child_a.state
    assert child_a.character_mechanics is not child_b.character_mechanics
    assert child_a.actions is original.actions
    assert child_a.execute_action("aemeath_basic_attack")
    assert future_state_fingerprint(original) == original_fp
    assert child_b.state.total_damage == original.state.total_damage
    before_b = future_state_fingerprint(child_b)
    assert child_b.execute_action("aemeath_echo_sigillum")
    assert future_state_fingerprint(child_a) != future_state_fingerprint(child_b)
    assert future_state_fingerprint(child_b) != before_b
    assert len(original.state.scheduled_effects) == 0
    print("beam_search_clone_isolation_smoke_test ok")


def _sim() -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
    )


if __name__ == "__main__":
    main()

