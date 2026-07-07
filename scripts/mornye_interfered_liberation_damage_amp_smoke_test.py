from __future__ import annotations

import sys
from pathlib import Path
import copy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


DATA_DIR = ROOT / "data"


def activate_interfered_marker(sim: Simulation) -> None:
    sim.state.target_interfered_state = "tune_rupture_interfered"
    sim.state.target_interfered_remaining = 8.0
    sim.state.interfered_marker_remaining = 8.0
    sim.state.interfered_marker_damage_taken_amp = 0.40


def run_liberation(*, marker: bool):
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = "fusion_burst"
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
        transition_config=config,
    )
    assert sim.execute_action("aemeath_basic_form_stage_3")
    sim.state.resonance_energy["aemeath"] = 125.0
    sim.state.character_states["aemeath"]["resonance_energy"] = 125.0
    sim.state.cooldowns.clear()
    if marker:
        activate_interfered_marker(sim)
    assert sim.execute_action("aemeath_liberation_overdrive")
    return sim.timeline[-1]


def main() -> None:
    baseline = run_liberation(marker=False)
    amped = run_liberation(marker=True)
    assert amped.normal_damage > baseline.normal_damage * 1.399
    assert amped.normal_damage < baseline.normal_damage * 1.401

    assert amped.action_type == "resonance_liberation"
    assert amped.damage_bonus_category == "resonance_liberation"
    assert amped.everbright_polestar_liberation_penetration_active is True
    assert amped.everbright_polestar_def_ignore_bonus == baseline.everbright_polestar_def_ignore_bonus
    assert amped.everbright_polestar_fusion_res_ignore_bonus == baseline.everbright_polestar_fusion_res_ignore_bonus

    hits = [hit for hit in amped.hit_details if hit.get("hit_damage_category") == "normal"]
    assert hits
    assert all(hit["target_damage_taken_amp"] == 0.40 for hit in hits)
    assert all(hit["target_damage_taken_amp_source"] == "mornye_interfered_marker" for hit in hits)
    assert all(hit["interfered_marker_amp_applied_to_direct_damage"] is True for hit in hits)
    assert all(hit["everbright_polestar_def_ignore_bonus"] == baseline.everbright_polestar_def_ignore_bonus for hit in hits)
    assert all(hit["everbright_polestar_fusion_res_ignore_bonus"] == baseline.everbright_polestar_fusion_res_ignore_bonus for hit in hits)
    assert all(hit["target_damage_taken_amp_bonus_damage"] > 0.0 for hit in hits)

    print("mornye_interfered_liberation_damage_amp_smoke_test ok")


if __name__ == "__main__":
    main()
