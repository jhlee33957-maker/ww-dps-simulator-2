from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def trigger_tune_strain_break(sim: Simulation) -> dict:
    sim.state.active_character_id = "aemeath"
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.enemy_mistune_active = True
    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max
    sim.state.target_tune_shift_state = "tune_strain_shifting"
    sim.state.target_tune_shift_remaining = 25.0
    assert sim.execute_action("aemeath_tune_break")
    return sim.state.action_log[-1]


def main() -> None:
    c0_sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    first = trigger_tune_strain_break(c0_sim)
    second = trigger_tune_strain_break(c0_sim)
    assert first["target_tune_strain_interfered_stacks"] == 1
    assert second["target_tune_strain_interfered_stacks"] == 1
    assert second["target_tune_strain_interfered_max_stacks"] == 1

    c2_sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    c2_sim.state.mechanics_config.setdefault("lynae", {})["lynae_constellation"] = 2
    trigger_tune_strain_break(c2_sim)
    c2_row = trigger_tune_strain_break(c2_sim)
    assert c2_row["target_tune_strain_interfered_stacks"] == 2
    assert c2_row["target_tune_strain_interfered_max_stacks"] == 2
    assert c2_row["lynae_spectral_analysis_c2_disabled_by_default"] is True

    c2_sim._advance_tune_break_runtime(29.0)
    assert c2_sim.state.target_tune_strain_interfered_stacks == 2
    assert c2_sim.state.target_tune_strain_interfered_remaining == 1.0
    c2_sim._advance_tune_break_runtime(1.1)
    assert c2_sim.state.target_interfered_state is None
    assert c2_sim.state.target_tune_strain_interfered_stacks == 0
    assert c2_sim.state.target_tune_strain_interfered_remaining == 0.0
    print("lynae_tune_strain_stack_duration_cap_smoke_test ok")


if __name__ == "__main__":
    main()
