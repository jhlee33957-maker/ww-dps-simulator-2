from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.observation_features import OBSERVATION_VERSION, build_observation_labels
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
EXPECTED = {
    "data/build_profiles.json": "fe0e46aaddb818ecd9b0180b3aa955671328a03c179e9dd5f8b9a7fc85506aa7",
    "data/weapons.json": "1e5595c9c9cb1b300d5f0e21b1f493b527f2868503511b6c1c467209b3c8df33",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    for rel, expected in EXPECTED.items():
        assert sha256(ROOT / rel) == expected
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_lynae_enabled_test_party", initial_active_character="mornye")
    assert OBSERVATION_VERSION == "slot_generic_mechanics_v5"
    assert len(build_observation_labels()) == 314
    assert len(sim.get_policy_action_ids()) == 25
    assert not sim.account_profile_gate_errors
    print("account_constellation_v121_benchmark_immutability_smoke_test ok")


if __name__ == "__main__":
    main()
