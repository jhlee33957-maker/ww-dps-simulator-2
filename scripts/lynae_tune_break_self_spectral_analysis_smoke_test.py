from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


ACTION_ID = "lynae_tune_break"


def ready_lynae_tune_break(shift_state: str) -> Simulation:
    sim = Simulation.from_json(
        ROOT / "data",
        party="aemeath_lynae_enabled_test_party",
        initial_active_character="lynae",
    )
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max
    sim.state.target_tune_shift_state = shift_state
    sim.state.target_tune_shift_remaining = 25.0
    return sim


def main() -> None:
    rupture = ready_lynae_tune_break("tune_rupture_shifting")
    assert rupture.execute_action(ACTION_ID)
    rupture_row = rupture.state.action_log[-1]
    assert rupture_row["tune_break_damage"] > 0.0
    assert rupture_row["target_interfered_state"] == "tune_rupture_interfered"
    assert rupture_row["lynae_spectral_analysis_triggered"] is True
    assert rupture_row["lynae_spectral_analysis_multiplier_used"] == 18.8075
    assert rupture_row["lynae_spectral_analysis_response_damage"] > 0.0

    strain = ready_lynae_tune_break("tune_strain_shifting")
    strain.state.character_mechanics_state["lynae"]["lynae_resonance_mode"] = "tune_strain"
    assert strain.execute_action(ACTION_ID)
    strain_row = strain.state.action_log[-1]
    assert strain_row["tune_break_damage"] > 0.0
    assert strain_row["target_interfered_state"] == "tune_strain_interfered"
    assert strain_row["target_tune_strain_interfered_stacks"] == 1
    assert strain_row["target_tune_strain_interfered_max_stacks"] == 1
    assert strain_row["target_tune_strain_interfered_remaining"] == 30.0
    assert strain_row["lynae_spectral_analysis_triggered"] is True
    assert strain_row["lynae_spectral_analysis_multiplier_used"] == 18.8075
    assert strain_row["lynae_spectral_analysis_response_damage"] > 0.0

    print("lynae_tune_break_self_spectral_analysis_smoke_test ok")


if __name__ == "__main__":
    main()
