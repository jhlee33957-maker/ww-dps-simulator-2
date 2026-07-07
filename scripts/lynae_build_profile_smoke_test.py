from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    lynae = sim.characters["lynae"]
    assert lynae.build_profile_id == "lynae_user_real_01"
    assert abs(lynae.effective_attack - 1931) < 1.0
    assert lynae.final_attack_reference == 1931
    assert lynae.attack_reference_delta is not None and abs(lynae.attack_reference_delta) < 1.0
    assert lynae.crit_rate == 0.974
    assert lynae.crit_damage == 2.088
    assert lynae.energy_regen == 1.516
    assert lynae.weapon["weapon_id"] == "static_mist"
    assert lynae.weapon["static_stats_already_in_profile"] is True
    assert lynae.weapon["energy_regen_already_in_profile"] is True
    print("lynae_build_profile_smoke_test ok")


if __name__ == "__main__":
    main()
