from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import ACCOUNT_SCOPE_ID, mornye_s3_distributed_array
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def main() -> None:
    sim = Simulation.from_json(
        DATA_DIR,
        selected_character_ids=["mornye"],
        build_profile_overrides={"mornye": "mornye_account_actual_01"},
        initial_active_character="mornye",
        account_simulation_scope=ACCOUNT_SCOPE_ID,
        precombat_elapsed_seconds=0,
    )
    assert not sim.account_profile_gate_errors
    state = {"mornye": {"sequence": 3}}
    first = mornye_s3_distributed_array(state, now=0.0)
    blocked = mornye_s3_distributed_array(state, now=24.9)
    ready = mornye_s3_distributed_array(state, now=25.0)
    assert first["concerto_gain"] == 25.0 and first["relative_momentum_gain"] == 100.0
    assert blocked["triggered"] is False
    assert ready["triggered"] is True
    print("mornye_s3_single_boss_v121_smoke_test ok")


if __name__ == "__main__":
    main()
