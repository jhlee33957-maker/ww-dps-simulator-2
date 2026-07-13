from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import clone_simulation_for_search  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    sim.combat_duration = 0.01
    sim.state.combat_duration = 0.01
    child = clone_simulation_for_search(sim)
    assert child.execute_action("aemeath_echo_sigillum")
    assert child.state.combat_time == 0.0
    before = child.state.total_damage
    assert child.execute_action("short_wait")
    assert child.state.combat_time == 0.01
    assert child.state.total_damage == before
    print("beam_search_cutoff_scheduler_smoke_test ok")


if __name__ == "__main__":
    main()

