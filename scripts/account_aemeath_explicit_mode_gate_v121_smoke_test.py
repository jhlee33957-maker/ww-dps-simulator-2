from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import ACCOUNT_BUILD_OVERRIDES, PARTY
from simulator.account_constellation_effects import ACCOUNT_SCOPE_ID
from simulator.account_profile_gate import AccountProfileSimulationBlocked
from simulator.simulation import Simulation


def _simulation() -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        selected_character_ids=PARTY,
        initial_active_character="aemeath",
        build_profile_overrides=ACCOUNT_BUILD_OVERRIDES,
        account_simulation_scope=ACCOUNT_SCOPE_ID,
        precombat_elapsed_seconds=5.0,
    )


def main() -> None:
    unresolved = _simulation()
    try:
        unresolved.execute_action("aemeath_sync_strike_armament_merge")
    except AccountProfileSimulationBlocked as exc:
        assert "aemeath_resonance_mode" in str(exc)
    else:
        raise AssertionError("unresolved account Aemeath mode executed")

    tune = _simulation()
    tune.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
    tune.validate_simulation_readiness(entry_point="explicit mode test")
    fusion = _simulation()
    fusion.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "fusion_burst"
    fusion.validate_simulation_readiness(entry_point="explicit mode test")
    print("account_aemeath_explicit_mode_gate_v121_smoke_test ok")


if __name__ == "__main__":
    main()
