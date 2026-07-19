from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
LIBERATION_ID = "lynae_resonance_liberation_prismatic_overblast"
VIVID_ID = "lynae_to_a_vivid_tomorrow"


def make_sim(initial: str = "lynae") -> Simulation:
    return Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character=initial,
    )


def execute_immediate_return_route() -> Simulation:
    sim = make_sim("mornye")
    assert sim.execute_action("swap_to_lynae")
    sim.state.resonance_energy["lynae"] = 125.0
    assert sim.execute_action(LIBERATION_ID)
    assert sim.execute_action(VIVID_ID)
    assert sim.execute_action("swap_to_mornye")
    return sim

