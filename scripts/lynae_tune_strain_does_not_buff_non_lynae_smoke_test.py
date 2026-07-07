from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.buff_system import apply_buff
from simulator.simulation import Simulation


def aemeath_basic_damage(with_lynae_tune_strain: bool) -> tuple[float, dict]:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    sim.state.active_character_id = "aemeath"
    if with_lynae_tune_strain:
        apply_buff(sim.state, sim.buffs["lynae_visual_impact_tune_break_boost"], "lynae")
        sim.state.target_interfered_state = "tune_strain_interfered"
        sim.state.target_interfered_remaining = 30.0
        sim.state.target_tune_strain_interfered_stacks = 1
        sim.state.target_tune_strain_interfered_max_stacks = 1
        sim.state.target_tune_strain_interfered_remaining = 30.0
    assert sim.execute_action("aemeath_basic_attack")
    row = sim.state.action_log[-1]
    return row["normal_damage"], row


def main() -> None:
    baseline_damage, _baseline = aemeath_basic_damage(False)
    tuned_damage, tuned_row = aemeath_basic_damage(True)
    assert math.isclose(tuned_damage, baseline_damage, rel_tol=0.0, abs_tol=1e-9)
    assert tuned_row["lynae_tune_strain_damage_amp_bonus_damage"] == 0.0
    assert all(
        float(detail.get("lynae_tune_strain_damage_amp_bonus_damage", 0.0) or 0.0) == 0.0
        for detail in tuned_row["hit_details"]
    )
    print("lynae_tune_strain_does_not_buff_non_lynae_smoke_test ok")


if __name__ == "__main__":
    main()
