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


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    initial_shape = len(build_observation_values(sim))
    sim.state.active_character_id = "lynae"
    state = sim.state.character_mechanics_state["lynae"]
    state["overflow"] = 120.0

    assert sim.execute_action("lynae_spark_collision")
    state = sim.state.character_mechanics_state["lynae"]
    values = observation(sim)
    assert state["overflow"] == 0.0
    assert state["lumiflow"] == 120.0
    assert state["kaleidoscopic_parade_remaining"] > 0.0
    assert values["slot_2.primary_resource_ratio"] == 0.0
    assert_close(values["slot_2.secondary_resource_ratio"], 1.0, "lumiflow ratio")
    assert values["slot_2.mechanic_state_0_active"] == 1.0
    assert values["slot_2.mechanic_state_0_remaining_ratio"] > 0.0

    assert sim.execute_action("lynae_polychrome_leap")
    state = sim.state.character_mechanics_state["lynae"]
    values = observation(sim)
    assert state["true_color"] == 1.0
    assert state["lumiflow"] == 80.0
    assert_close(values["slot_2.tertiary_resource_ratio"], 1.0 / 3.0, "true color ratio")
    assert values["slot_2.secondary_resource_ratio"] < 1.0
    assert len(build_observation_values(sim)) == initial_shape
    print("lynae_observation_kaleidoscopic_state_smoke_test ok")


if __name__ == "__main__":
    main()
