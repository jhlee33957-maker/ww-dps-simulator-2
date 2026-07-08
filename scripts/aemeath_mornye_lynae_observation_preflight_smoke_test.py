from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.observation_features import (
    build_observation_channel_mapping,
    build_observation_labels,
    build_observation_slot_mapping,
    build_observation_values,
)
from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def observation(sim: Simulation) -> dict[str, float]:
    return dict(zip(build_observation_labels(), build_observation_values(sim), strict=True))


def set_full_concerto(sim: Simulation, character_id: str) -> None:
    sim.state.concerto_energy[character_id] = 100.0
    sim.state.character_states[character_id]["concerto_energy"] = 100.0
    sim.state.character_states[character_id]["concerto_ready"] = True


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    initial_shape = len(build_observation_values(sim))
    mapping = build_observation_channel_mapping(sim)
    slot_mapping = build_observation_slot_mapping(sim)
    assert slot_mapping["slot_2"] == "lynae"
    assert mapping["slot_2.primary_resource_ratio"] == "lynae_overflow"
    assert mapping["slot_2.tune_response_0"] == "lynae_spectral_analysis"
    before = observation(sim)
    assert before["slot_2.primary_resource_ratio"] == 0.0

    sim.state.active_character_id = "aemeath"
    set_full_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_lynae")
    after_intro = observation(sim)
    assert after_intro["slot_2.primary_resource_ratio"] > before["slot_2.primary_resource_ratio"]
    assert after_intro["slot_2.mechanic_state_2_active"] == 1.0

    assert sim.execute_action("lynae_basic_attack")
    after_basic = observation(sim)
    assert after_basic["slot_2.primary_resource_ratio"] > after_intro["slot_2.primary_resource_ratio"]

    sim.state.character_mechanics_state["lynae"]["overflow"] = 120.0
    assert sim.execute_action("lynae_spark_collision")
    after_spark = observation(sim)
    assert after_spark["slot_2.primary_resource_ratio"] == 0.0
    assert after_spark["slot_2.secondary_resource_ratio"] == 1.0
    assert after_spark["slot_2.mechanic_state_0_active"] == 1.0
    assert len(build_observation_values(sim)) == initial_shape
    print("aemeath_mornye_lynae_observation_preflight_smoke_test ok")


if __name__ == "__main__":
    main()
