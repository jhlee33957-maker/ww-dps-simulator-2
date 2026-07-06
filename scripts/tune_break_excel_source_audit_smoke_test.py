from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    md = ROOT / "reports" / "tune_break_excel_source_audit.md"
    js = ROOT / "data" / "extracted" / "tune_break_excel_source_audit.json"
    runtime_md = ROOT / "reports" / "tune_break_system_runtime_note.md"
    runtime_js = ROOT / "data" / "extracted" / "tune_break_system_runtime_note.json"
    for path in (md, js, runtime_md, runtime_js):
        assert path.exists(), path

    audit = json.loads(js.read_text(encoding="utf-8"))
    assert audit["enemy_off_tune_max_default"] == 3920
    assert audit["off_tune_value_column"]["column"] == "S"
    assert audit["aemeath_tune_break"]["action_rows"]
    assert audit["mornye_tune_break"]["action_rows"]
    assert audit["mornye_observation_marker_interfered_marker"]["ref"] == "角色-女!D4164"
    assert "multi-target marker tracking" in audit["unsupported_full_mechanics"]
    assert audit["aemeath_starburst_response"]["damage_source_status"] == "workbook_confirmed"
    assert audit["mornye_particle_jet_response"]["damage_source_status"] == "workbook_confirmed"
    assert audit["response_event_order"]["response_triggers_without_observation_marker"] is True
    assert audit["response_event_order"]["response_amp_timing_source_status"] == "excel_event_order_derived"
    assert audit["unresolved"].get("tune_break_cooldown") != "not_found_uses_explicit_default_8s"
    assert audit["enemy_tune_break_cooldown_seconds"] == 3.0
    assert audit["enemy_tune_break_cooldown_source_status"] == "workbook_confirmed_cost4_red_name_boss_default"
    assert audit["cooldown_blocks_off_tune_accumulation"] is True
    assert "starburst" in md.read_text(encoding="utf-8").lower()

    runtime = json.loads(runtime_js.read_text(encoding="utf-8"))
    assert runtime["tune_break_action_model"] == "conditional_character_specific_policy_action_not_automatic_damage"
    assert runtime["response_damage_status"] == "workbook_confirmed"
    assert "response event order" in runtime_md.read_text(encoding="utf-8").lower()

    print("tune_break_excel_source_audit_smoke_test ok")


if __name__ == "__main__":
    main()
