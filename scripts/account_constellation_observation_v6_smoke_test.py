from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.observation_features import OBSERVATION_VERSION, build_observation_labels
from simulator.account_constellation_effects import (
    ACCOUNT_OBSERVATION_SHAPE,
    ACCOUNT_OBSERVATION_VERSION,
    ACCOUNT_SCOPE_ID,
    build_account_observation_labels,
    build_account_observation_values,
    initialize_account_constellation_state,
)
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def main() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_lynae_enabled_test_party", initial_active_character="mornye")
    assert OBSERVATION_VERSION == "slot_generic_mechanics_v5"
    assert len(build_observation_labels()) == 314
    assert len(sim.get_policy_action_ids()) == 25
    assert ACCOUNT_OBSERVATION_VERSION == "slot_account_constellation_single_boss_v6"
    labels = build_account_observation_labels()
    state = initialize_account_constellation_state({"aemeath": {"sequence": 6}, "lynae": {"sequence": 2}}, ACCOUNT_SCOPE_ID, 4.5, optical_sampling_active=True)
    values = build_account_observation_values(state)
    assert len(labels) == ACCOUNT_OBSERVATION_SHAPE == 330
    assert len(values) == 330
    assert "account_precombat.aemeath_radiance_ready" in labels
    print("account_constellation_observation_v6_smoke_test ok")


if __name__ == "__main__":
    main()
