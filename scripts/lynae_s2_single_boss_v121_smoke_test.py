from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import ACCOUNT_SCOPE_ID, lynae_s2_collective_interference_cap, lynae_s2_outro_totals, lynae_s2_self_deepen
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def main() -> None:
    sim = Simulation.from_json(
        DATA_DIR,
        selected_character_ids=["lynae"],
        build_profile_overrides={"lynae": "lynae_account_actual_01"},
        initial_active_character="lynae",
        account_simulation_scope=ACCOUNT_SCOPE_ID,
        precombat_elapsed_seconds=0,
    )
    assert not sim.account_profile_gate_errors
    assert lynae_s2_self_deepen() == 0.25
    totals = lynae_s2_outro_totals()
    assert totals["general_all_damage_deepen_total"] == 0.40
    assert totals["liberation_total_deepen"] == 0.65
    assert lynae_s2_collective_interference_cap(2) == 3
    print("lynae_s2_single_boss_v121_smoke_test ok")


if __name__ == "__main__":
    main()
