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
MORNYE_LIBERATION_ID = "mornye_liberation_critical_protocol"


def make_sim(initial: str = "lynae") -> Simulation:
    return Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character=initial,
    )


def set_mornye_observation_state(sim: Simulation, active: bool) -> None:
    state = sim.state.character_mechanics_state["mornye"]
    state["observation_marker_active"] = bool(active)
    state["observation_marker_remaining"] = 30.0 if active else 0.0


def make_mornye_liberation_sim(observation_active: bool) -> Simulation:
    sim = make_sim("mornye")
    sim.state.resonance_energy["mornye"] = 175.0
    sim.state.concerto_energy["mornye"] = 0.0
    sim.state.character_mechanics_state["mornye"]["syntony_field_remaining"] = 10.0
    set_mornye_observation_state(sim, observation_active)
    return sim


def execute_immediate_return_route() -> Simulation:
    sim = make_sim("mornye")
    assert sim.execute_action("swap_to_lynae")
    sim.state.resonance_energy["lynae"] = 125.0
    assert sim.execute_action(LIBERATION_ID)
    assert sim.execute_action(VIVID_ID)
    assert sim.execute_action("swap_to_mornye")
    return sim
