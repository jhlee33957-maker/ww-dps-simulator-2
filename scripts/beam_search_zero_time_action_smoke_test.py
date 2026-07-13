from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import clone_simulation_for_search, future_state_fingerprint  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    assert "aemeath_echo_sigillum" in sim.valid_action_ids()
    before_combat = sim.state.combat_time
    before_fp = future_state_fingerprint(sim)
    child = clone_simulation_for_search(sim)
    assert child.execute_action("aemeath_echo_sigillum")
    assert child.state.combat_time == before_combat
    assert future_state_fingerprint(child) != before_fp
    assert not child.execute_action("aemeath_echo_sigillum")
    print("beam_search_zero_time_action_smoke_test ok")


if __name__ == "__main__":
    main()

