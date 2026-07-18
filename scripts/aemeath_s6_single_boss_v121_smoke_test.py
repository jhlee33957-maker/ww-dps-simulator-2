from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import (
    ACCOUNT_SCOPE_ID,
    aemeath_s6_fixed_crit_expected_multiplier,
    aemeath_s6_liberation_deepen,
    initialize_account_constellation_state,
)
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def main() -> None:
    sim = Simulation.from_json(
        DATA_DIR,
        selected_character_ids=["aemeath"],
        build_profile_overrides={"aemeath": "aemeath_account_actual_01"},
        initial_active_character="aemeath",
        account_simulation_scope=ACCOUNT_SCOPE_ID,
        precombat_elapsed_seconds=0,
    )
    assert not sim.account_profile_gate_errors
    assert sim.account_constellation_state is not None
    assert sim.account_constellation_diagnostics["scope_id"] == ACCOUNT_SCOPE_ID
    assert aemeath_s6_liberation_deepen("aemeath", "resonance_liberation") == 0.40
    assert aemeath_s6_liberation_deepen("lynae", "resonance_liberation") == 0.0
    assert math.isclose(aemeath_s6_fixed_crit_expected_multiplier(), 2.4, abs_tol=1e-12)
    state = initialize_account_constellation_state(sim.characters, ACCOUNT_SCOPE_ID, 0)
    assert state["aemeath"]["sequence"] == 6
    print("aemeath_s6_single_boss_v121_smoke_test ok")


if __name__ == "__main__":
    main()
