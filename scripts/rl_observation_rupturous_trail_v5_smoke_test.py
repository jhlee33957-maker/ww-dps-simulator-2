from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.observation_features import OBSERVATION_VERSION, build_observation_channel_mapping, build_observation_labels, build_observation_values
from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    sim.state.rupturous_trail_stacks = 15
    sim.state.rupturous_trail_remaining = 12.0
    labels = build_observation_labels()
    values = build_observation_values(sim)
    assert OBSERVATION_VERSION == "slot_generic_mechanics_v5"
    assert len(labels) == 314
    assert len(values) == 314
    stack_index = labels.index("global.target_rupturous_trail_stack_ratio")
    remaining_index = labels.index("global.target_rupturous_trail_remaining_ratio")
    assert values[stack_index] == 0.5
    assert values[remaining_index] == 0.4
    assert build_observation_channel_mapping(sim)["global.target_rupturous_trail"] == "aemeath_c0_rupturous_trail_target_state"
    print("rl_observation_rupturous_trail_v5_smoke_test ok")


if __name__ == "__main__":
    main()
