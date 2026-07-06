from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data = json.loads((ROOT / "data" / "tune_responses.json").read_text(encoding="utf-8"))
    responses = {item["id"]: item for item in data}
    assert responses["aemeath_starburst"]["multiplier"] == 5.9643
    assert responses["mornye_particle_jet"]["multiplier"] == 2.9822
    assert responses["mornye_particle_jet"]["c5_multiplier"] == 7.7536
    assert responses["mornye_particle_jet"]["policy_selectable"] is False

    audit = json.loads((ROOT / "data" / "extracted" / "tune_break_excel_source_audit.json").read_text(encoding="utf-8"))
    assert audit["aemeath_starburst_response"]["damage_source_status"] == "workbook_confirmed"
    assert audit["aemeath_starburst_response"]["refs"] == [
        "角色-女!D2844",
        "角色-女!C2880:D2880",
        "角色技能类型!A2737:I2737",
        "dmg!A2590:C2590",
    ]
    assert audit["mornye_particle_jet_response"]["c0_multiplier"] == 2.9822
    assert audit["mornye_particle_jet_response"]["c5_multiplier"] == 7.7536
    assert audit["response_event_order"]["source_status"] == "excel_event_order_derived"
    assert audit["response_event_order"]["response_amp_timing_source_status"] == "excel_event_order_derived"
    assert audit["response_event_order"]["tune_response_damage_formula_source_status"] == "workbook_confirmed"
    assert audit["response_event_order"]["tune_break_damage_receives_new_interfered_marker_amp"] is False
    assert audit["response_event_order"]["response_triggers_without_observation_marker"] is True
    assert audit["unresolved"].get("tune_break_cooldown") != "not_found_uses_explicit_default_8s"
    assert audit["enemy_tune_break_cooldown_seconds"] == 3.0
    assert audit["enemy_tune_break_cooldown_source_status"] == "workbook_confirmed_cost4_red_name_boss_default"
    assert audit["enemy_tune_break_cooldown_source_ref"] in {"附页2!B227", "?꾦〉2!B227"}

    runtime = json.loads(
        (ROOT / "data" / "extracted" / "tune_break_system_runtime_note.json").read_text(encoding="utf-8")
    )
    assert runtime["response_damage_status"] == "workbook_confirmed"
    assert runtime["response_amp_timing_source_status"] == "excel_event_order_derived"
    assert runtime["tune_response_damage_formula_source_status"] == "workbook_confirmed"
    assert runtime["response_damage_receives_new_interfered_marker_amp_if_marker_applied_before_response"] is True

    print("tune_response_source_audit_smoke_test ok")


if __name__ == "__main__":
    main()
