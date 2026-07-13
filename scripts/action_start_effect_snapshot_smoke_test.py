from __future__ import annotations

import copy
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.combat_time_effect_duration_smoke_test import (
    PARTY_ID,
    active_buff,
    setup_interfered_marker,
)
from simulator.models import AnomalyState
from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


DATA_DIR = ROOT / "data"
INTERFERED_BUFF_ID = "mornye_interfered_marker_damage_amp"
EVERBRIGHT_BUFF_ID = "everbright_polestar_liberation_penetration"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def aemeath_party_sim(initial_active: str = "aemeath") -> Simulation:
    return Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character=initial_active)


def aemeath_base_damage_pair() -> tuple[float, float]:
    sim = aemeath_party_sim()
    assert sim.execute_action("aemeath_basic_attack")
    first = sim.timeline[-1].damage
    assert sim.execute_action("aemeath_basic_attack")
    return first, sim.timeline[-1].damage


def aemeath_marker_damage(remaining: float | None = None) -> tuple[Simulation, float]:
    sim = aemeath_party_sim("mornye")
    setup_interfered_marker(sim)
    if remaining is not None:
        sim.state.interfered_marker_remaining = remaining
        sim.state.target_interfered_remaining = remaining
        active_buff(sim, INTERFERED_BUFF_ID).remaining_duration = remaining
    sim.state.active_character_id = "aemeath"
    assert sim.execute_action("aemeath_basic_attack")
    return sim, sim.timeline[-1].damage


def test_interfered_marker_deduplicates_action_start_snapshot() -> None:
    base_first, base_second = aemeath_base_damage_pair()
    full, full_damage = aemeath_marker_damage()
    short, short_damage = aemeath_marker_damage(0.1)

    expected_multiplier = 1.0 + 0.3856
    duplicate_multiplier = expected_multiplier * expected_multiplier
    assert_close(full_damage / base_first, expected_multiplier, "full marker ratio", tolerance=1e-7)
    assert_close(short_damage / base_first, expected_multiplier, "short marker ratio", tolerance=1e-7)
    assert not math.isclose(short_damage / base_first, duplicate_multiplier, rel_tol=0.0, abs_tol=1e-7)
    assert not any(buff.buff_id == INTERFERED_BUFF_ID for buff in short.state.active_buffs)
    assert short.execute_action("aemeath_basic_attack")
    assert_close(short.timeline[-1].damage, base_second, "following action after marker expiry", tolerance=1e-6)
    assert full.timeline[-1].interfered_marker_direct_damage_amp_applied_count == 1
    assert short.timeline[2].interfered_marker_direct_damage_amp_applied_count == 1


def havoc_sim(remaining: float) -> Simulation:
    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["main", "sub", "support"])
    sim.state.active_anomalies["havoc_bane"] = AnomalyState(
        anomaly_type="havoc_bane",
        stacks=5,
        remaining_duration=remaining,
        tick_interval=1.0,
        tick_timer=1.0,
    )
    return sim


def test_havoc_bane_action_start_snapshot() -> None:
    full = havoc_sim(8.0)
    short = havoc_sim(0.1)
    assert full.execute_action("main_resonance_liberation")
    assert short.execute_action("main_resonance_liberation")
    full_row = full.timeline[-1]
    short_row = short.timeline[-1]
    assert_close(short_row.damage, full_row.damage, "short Havoc Bane full-action damage", tolerance=1e-6)
    assert all(hit["applied_havoc_bane_def_reduction"] > 0.0 for hit in short_row.hit_details)
    assert "havoc_bane" not in short.state.active_anomalies

    baseline = Simulation.from_json(DATA_DIR, selected_character_ids=["main", "sub", "support"])
    assert baseline.execute_action("main_basic_attack")
    assert short.execute_action("main_basic_attack")
    assert_close(short.timeline[-1].damage, baseline.timeline[-1].damage, "following action after Havoc expiry", tolerance=1e-6)


def everbright_transition_config() -> dict:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = "fusion_burst"
    return config


def everbright_sim() -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
        transition_config=everbright_transition_config(),
    )
    sim.characters["aemeath"].weapon["rank"] = 1
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert any(buff.buff_id == EVERBRIGHT_BUFF_ID for buff in sim.state.active_buffs)
    return sim


def test_everbright_polestar_action_start_snapshot() -> None:
    full = everbright_sim()
    short = everbright_sim()
    active_buff(short, EVERBRIGHT_BUFF_ID).remaining_duration = 0.1

    assert full.execute_action("aemeath_heavy_aemeath_charged_1")
    assert short.execute_action("aemeath_heavy_aemeath_charged_1")
    full_row = full.timeline[-1]
    short_row = short.timeline[-1]
    assert full_row.everbright_polestar_liberation_penetration_active is True
    assert short_row.everbright_polestar_liberation_penetration_active is True
    assert_close(short_row.damage, full_row.damage, "short Everbright full-action damage", tolerance=1e-6)
    assert not any(buff.buff_id == EVERBRIGHT_BUFF_ID for buff in short.state.active_buffs)

    short.state.cooldowns.clear()
    assert short.execute_action("aemeath_heavy_aemeath_charged_1")
    assert short.timeline[-1].everbright_polestar_liberation_penetration_active is False


def main() -> None:
    test_interfered_marker_deduplicates_action_start_snapshot()
    test_havoc_bane_action_start_snapshot()
    test_everbright_polestar_action_start_snapshot()
    print("action_start_effect_snapshot_smoke_test ok")


if __name__ == "__main__":
    main()
