from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.echo_sets import apply_syntony_field_off_tune_buff
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
TIMING_MODE = "same_action_high_syntony_field_creation_approximation"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert math.isclose(actual, expected, rel_tol=tol, abs_tol=tol), f"{label}: expected {expected}, got {actual}"


def make_sim() -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        initial_active_character="mornye",
        build_profile_overrides={"mornye": "mornye_user_real_01"},
        transition_config={"mechanics": {"mornye": {"mornye_heal_event_mode": "simplified_syntony_field_uptime"}}},
    )
    sim.state.resonance_energy["mornye"] = sim.characters["mornye"].resonance_energy_max
    sim.state.character_states["mornye"]["syntony_field_remaining"] = 25.0
    apply_syntony_field_off_tune_buff(state=sim.state, constellation=0)
    return sim


def test_critical_protocol_same_action_high_syntony_logs() -> None:
    sim = make_sim()
    expected_def = sim.characters["mornye"].static_def + sim.characters["mornye"].base_def_total * 0.20

    assert sim.execute_action("mornye_resonance_liberation")
    row = sim.timeline[-1]
    damage_log = sim.state.damage_log[-1]

    assert row.resolved_action_id == "mornye_liberation_critical_protocol"
    assert row.critical_protocol_high_syntony_created_before_damage is True
    assert row.high_syntony_field_same_action_application is True
    assert row.high_syntony_field_application_timing == TIMING_MODE
    assert row.high_syntony_field_def_bonus_active is True
    assert_close(row.runtime_def_percent_bonus, 0.20, "row runtime DEF")
    assert row.high_syntony_field_off_tune_inherited is True
    assert row.high_syntony_field_heal_proxy_active is True
    assert_close(row.effective_def, expected_def, "row effective DEF")
    assert row.halo_of_starry_radiance_5set_active is True
    assert row.halo_atk_buff_does_not_affect_mornye_def_damage is True
    assert row.scaling_stat == "def"
    assert row.normal_damage > 0.0
    assert row.anomaly_damage == 0.0

    for key in (
        "critical_protocol_high_syntony_created_before_damage",
        "high_syntony_field_same_action_application",
        "high_syntony_field_application_timing",
        "high_syntony_field_def_bonus_active",
        "runtime_def_percent_bonus",
        "high_syntony_field_off_tune_inherited",
        "high_syntony_field_heal_proxy_active",
        "effective_def",
        "halo_of_starry_radiance_5set_active",
        "halo_atk_buff_does_not_affect_mornye_def_damage",
    ):
        assert damage_log[key] == getattr(row, key), key

    normal_details = [detail for detail in row.hit_details if detail.get("hit_damage_category") == "normal"]
    assert normal_details
    for detail in normal_details:
        assert detail["critical_protocol_high_syntony_created_before_damage"] is True
        assert detail["high_syntony_field_same_action_application"] is True
        assert detail["high_syntony_field_application_timing"] == TIMING_MODE
        assert detail["high_syntony_field_def_bonus_active"] is True
        assert_close(detail["runtime_def_percent_bonus"], 0.20, "detail runtime DEF")
        assert_close(detail["effective_def"], expected_def, "detail effective DEF")
        assert detail["high_syntony_field_off_tune_inherited"] is True
        assert detail["high_syntony_field_heal_proxy_active"] is True
        assert detail["halo_of_starry_radiance_5set_active"] is True
        assert detail["halo_atk_buff_does_not_affect_mornye_def_damage"] is True
        assert detail["scaling_stat"] == "def"

    assert all("fusion_burst" not in tag for tag in row.emitted_mechanic_event_tags)
    assert all(float(event.get("damage_added", 0.0)) == 0.0 for event in sim.state.mechanic_event_log)
    assert all(log["action_id"] != "mornye_syntony_field_damage" for log in sim.state.damage_log)


def main() -> None:
    test_critical_protocol_same_action_high_syntony_logs()
    print("mornye_critical_protocol_same_action_high_field_smoke_test ok")


if __name__ == "__main__":
    main()
