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
    assert audit["unresolved"]["exact_starburst_damage"] == "unresolved_no_damage_invented"
    assert "unresolved" in md.read_text(encoding="utf-8").lower()

    runtime = json.loads(runtime_js.read_text(encoding="utf-8"))
    assert runtime["tune_break_action_model"] == "conditional_character_specific_policy_action_not_automatic_damage"
    assert runtime["response_damage_status"] == "unresolved_no_damage_invented"

    print("tune_break_excel_source_audit_smoke_test ok")


if __name__ == "__main__":
    main()
