from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.observation_features import build_observation_labels, build_observation_values
from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def observation(sim: Simulation) -> dict[str, float]:
    return dict(zip(build_observation_labels(), build_observation_values(sim), strict=True))


def set_full_concerto(sim: Simulation, character_id: str) -> None:
    sim.state.concerto_energy[character_id] = 100.0
    sim.state.character_states[character_id]["concerto_energy"] = 100.0
    sim.state.character_states[character_id]["concerto_ready"] = True


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    initial_shape = len(build_observation_values(sim))
    sim.state.active_character_id = "aemeath"
    set_full_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_lynae")

    state = sim.state.character_mechanics_state["lynae"]
    values = observation(sim)
    assert state["overflow"] == 100.0
    assert state["photocromic_flux_active"] is True
    assert state["target_tune_shift_state"] == "tune_rupture_shifting"
    assert_close(values["slot_2.primary_resource_ratio"], 100.0 / 120.0, "overflow ratio")
    assert values["slot_2.mechanic_state_2_active"] == 1.0
    assert values["slot_2.mechanic_state_2_remaining_ratio"] > 0.0
    assert values["global.target_tune_shift_state_rupture_active"] == 1.0
    assert len(build_observation_values(sim)) == initial_shape

    assert sim.execute_action("lynae_basic_attack")
    state = sim.state.character_mechanics_state["lynae"]
    values = observation(sim)
    assert state["overflow"] == 112.0
    assert_close(values["slot_2.primary_resource_ratio"], 112.0 / 120.0, "overflow ratio after basic")
    assert len(build_observation_values(sim)) == initial_shape
    print("lynae_observation_after_intro_smoke_test ok")


if __name__ == "__main__":
    main()
