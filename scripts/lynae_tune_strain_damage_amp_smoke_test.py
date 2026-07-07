from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.buff_system import apply_buff
from simulator.action_executor import _calculate_hit_damage
from simulator.models import HitData
from simulator.simulation import Simulation


def main() -> None:
    direct_sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    apply_buff(direct_sim.state, direct_sim.buffs["lynae_visual_impact_tune_break_boost"], "lynae")
    direct_sim.state.active_character_id = "lynae"
    direct_sim.state.target_interfered_state = "tune_strain_interfered"
    direct_sim.state.target_interfered_remaining = 30.0
    direct_sim.state.target_tune_strain_interfered_stacks = 1
    direct_sim.state.target_tune_strain_interfered_max_stacks = 1
    direct_sim.state.target_tune_strain_interfered_remaining = 30.0
    assert direct_sim.execute_action("lynae_basic_attack")
    direct_row = direct_sim.state.action_log[-1]
    assert direct_row["normal_damage"] > 0.0
    assert math.isclose(direct_row["lynae_tune_strain_damage_amp"], 0.048, rel_tol=0.0, abs_tol=1e-12)
    assert direct_row["lynae_tune_strain_damage_amp_bonus_damage"] > 0.0

    tune_break_sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    apply_buff(tune_break_sim.state, tune_break_sim.buffs["lynae_visual_impact_tune_break_boost"], "lynae")
    tune_break_sim.state.active_character_id = "lynae"
    tune_break_sim.state.target_interfered_state = "tune_strain_interfered"
    tune_break_sim.state.target_interfered_remaining = 30.0
    tune_break_sim.state.target_tune_strain_interfered_stacks = 1
    tune_break_sim.state.target_tune_strain_interfered_max_stacks = 1
    tune_break_sim.state.target_tune_strain_interfered_remaining = 30.0
    tune_break_damage, tune_break_detail = _calculate_hit_damage(
        HitData(time=0.0, damage_category="tune_break", tune_break_multiplier=1.0, name="synthetic_lynae_tune_break"),
        tune_break_sim.actions["lynae_tune_break"],
        tune_break_sim.state,
        tune_break_sim.characters,
        tune_break_sim.buffs,
    )
    assert tune_break_damage > 0.0
    assert math.isclose(tune_break_detail["lynae_tune_strain_damage_amp"], 0.048, rel_tol=0.0, abs_tol=1e-12)
    assert tune_break_detail["lynae_tune_strain_damage_amp_bonus_damage"] > 0.0

    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    apply_buff(sim.state, sim.buffs["lynae_visual_impact_tune_break_boost"], "lynae")
    sim.state.active_character_id = "aemeath"
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max
    sim.state.target_tune_shift_state = "tune_strain_shifting"
    sim.state.target_tune_shift_remaining = 25.0

    assert sim.execute_action("aemeath_tune_break")
    row = sim.state.action_log[-1]
    detail = next(
        detail
        for detail in row["tune_response_hit_details"]
        if detail.get("tune_response_id") == "lynae_spectral_analysis"
    )
    assert detail["target_tune_strain_interfered_stacks"] == 1
    assert detail["current_tune_break_boost_points"] == 40.0
    assert math.isclose(detail["lynae_tune_strain_damage_amp"], 0.048, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(detail["lynae_tune_strain_damage_multiplier"], 1.048, rel_tol=0.0, abs_tol=1e-12)
    assert detail["lynae_tune_strain_damage_amp_bonus_damage"] > 0.0
    assert row["lynae_tune_strain_damage_amp_bonus_damage"] == detail["lynae_tune_strain_damage_amp_bonus_damage"]
    assert detail["lynae_tune_strain_source_status"] == "user_tooltip_confirmed_single_target"
    assert detail["lynae_tune_strain_source_ref"] == "角色-女!2728"
    print("lynae_tune_strain_damage_amp_smoke_test ok")


if __name__ == "__main__":
    main()
