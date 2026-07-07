from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    state = sim.state.character_mechanics_state["lynae"]
    state["lynae_resonance_mode"] = "tune_strain"
    state["overflow"] = 120.0
    assert sim.execute_action("lynae_spark_collision")
    assert sim.execute_action("lynae_polychrome_leap_stage_1")
    assert sim.state.target_tune_shift_state == "tune_strain_shifting"
    sim.state.active_character_id = "aemeath"
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max
    assert sim.execute_action("aemeath_tune_break")
    row = sim.state.action_log[-1]
    assert row["target_interfered_state"] == "tune_strain_interfered"
    assert row["lynae_spectral_analysis_triggered"] is True
    assert row["lynae_spectral_analysis_multiplier_used"] == 18.8075
    print("lynae_tune_strain_flux_to_spectral_analysis_smoke_test ok")


if __name__ == "__main__":
    main()
