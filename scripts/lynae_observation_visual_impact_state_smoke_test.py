from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.observation_features import build_observation_labels, build_observation_values
from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def observation(sim: Simulation) -> dict[str, float]:
    return dict(zip(build_observation_labels(), build_observation_values(sim), strict=True))


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    initial_shape = len(build_observation_values(sim))
    sim.state.active_character_id = "lynae"
    state = sim.state.character_mechanics_state["lynae"]
    state["overflow"] = 120.0
    assert sim.execute_action("lynae_spark_collision")
    for _ in range(3):
        assert sim.execute_action("lynae_polychrome_leap")
    state = sim.state.character_mechanics_state["lynae"]
    assert state["true_color"] == 3.0

    assert sim.execute_action("lynae_visual_impact")
    state = sim.state.character_mechanics_state["lynae"]
    values = observation(sim)
    assert state["true_color"] == 0.0
    assert state["visual_impact_cooldown_remaining"] > 0.0
    assert state["spray_paint_window_remaining"] > 0.0
    assert state["photocromic_flux_active"] is True
    assert values["slot_2.tertiary_resource_ratio"] == 0.0
    assert values["slot_2.mechanic_state_4_active"] == 1.0
    assert values["slot_2.mechanic_state_5_active"] == 1.0
    assert values["slot_2.mechanic_state_2_active"] == 1.0
    assert len(build_observation_values(sim)) == initial_shape
    print("lynae_observation_visual_impact_state_smoke_test ok")


if __name__ == "__main__":
    main()
