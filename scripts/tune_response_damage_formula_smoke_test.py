from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.tune_break import calculate_tune_response_damage_detail


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-6) -> None:
    assert abs(actual - expected) <= tol, f"{label}: {actual} != {expected}"


def main() -> None:
    detail = calculate_tune_response_damage_detail(
        tune_response_id="aemeath_starburst",
        tune_response_hit_id="aemeath_starburst_1",
        tune_response_multiplier=5.9643,
        additional_tune_response_boost=0.2,
        tune_dmg_bonus=0.1,
        enemy_res=0.1,
        res_pen=0.0,
        attacker_level=90,
        enemy_level=90,
        applied_damage_taken_amp=0.4,
        tune_response_element="fusion",
    )
    expected = 10000.0 * 5.9643 * 1.2 * 0.9 * detail["tune_response_def_multiplier"] * 1.1 * 1.4
    assert detail["is_tune_response_damage"] is True
    assert detail["tune_response_base_value"] == 10000.0
    assert detail["tune_response_multiplier"] == 5.9643
    assert detail["tune_response_element"] == "fusion"
    assert detail["tune_response_raw_damage_type"] == "tune_break_response"
    assert detail["applied_damage_taken_amp"] == 0.4
    assert detail["response_damage_receives_interfered_marker_amp"] is True
    assert detail["response_damage_receives_newly_applied_interfered_marker_amp"] is False
    assert detail["response_damage_receives_existing_interfered_marker_amp"] is False
    assert detail["response_damage_receives_new_interfered_marker_amp"] is False
    assert detail["source_status"] == "workbook_confirmed"
    assert_close(detail["tune_response_damage"], expected, "response damage")

    c0 = calculate_tune_response_damage_detail(
        tune_response_id="mornye_particle_jet",
        tune_response_hit_id="mornye_particle_jet_1",
        tune_response_multiplier=2.9822,
        enemy_res=0.1,
        res_pen=0.0,
        attacker_level=90,
        enemy_level=90,
    )
    c5 = calculate_tune_response_damage_detail(
        tune_response_id="mornye_particle_jet",
        tune_response_hit_id="mornye_particle_jet_1",
        tune_response_multiplier=7.7536,
        enemy_res=0.1,
        res_pen=0.0,
        attacker_level=90,
        enemy_level=90,
    )
    assert c5["tune_response_damage"] > c0["tune_response_damage"] * 2.5

    print("tune_response_damage_formula_smoke_test ok")


if __name__ == "__main__":
    main()
