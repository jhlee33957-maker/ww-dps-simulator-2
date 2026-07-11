from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    runpy.run_path(str(ROOT / "scripts/lynae_source_audit.py"), run_name="__main__")
    action_map_path = ROOT / "data/extracted/lynae_excel_action_map.json"
    unresolved_path = ROOT / "data/extracted/lynae_excel_unresolved_rows.json"
    off_tune_audit_path = ROOT / "data/extracted/lynae_off_tune_direct_mapping_audit.json"
    report_path = ROOT / "reports/lynae_excel_source_alignment.md"
    off_tune_report_path = ROOT / "reports/lynae_off_tune_direct_mapping_audit.md"
    assert action_map_path.exists()
    assert unresolved_path.exists()
    assert off_tune_audit_path.exists()
    assert report_path.exists()
    assert off_tune_report_path.exists()

    action_map = json.loads(action_map_path.read_text(encoding="utf-8"))
    by_id = {item["action_id"]: item for item in action_map}
    assert by_id["lynae_spark_collision_lv3"]["damage_rows"] == [2421, 2422]
    assert abs(by_id["lynae_spark_collision_lv3"]["multiplier"] - 5.5556) < 1e-9
    assert by_id["lynae_visual_impact"]["damage_rows"] == [2464, 2465]
    assert abs(by_id["lynae_visual_impact"]["multiplier"] - 12.1672) < 1e-9
    assert by_id["lynae_visual_impact"]["calculation_type"] == "mutually_exclusive_mode_variants_same_multiplier"
    assert abs(by_id["lynae_iridescent_splash"]["multiplier"] - 3.0418) < 1e-9
    assert by_id["lynae_iridescent_splash"]["calculation_type"] == "mutually_exclusive_mode_variants_same_multiplier"
    assert abs(by_id["lynae_intro_time_to_show_some_colors"]["multiplier"] - 2.2480) < 1e-9
    assert abs(by_id["lynae_resonance_liberation_prismatic_overblast"]["multiplier"] - 8.7480) < 1e-9
    assert abs(by_id["lynae_tune_response_spectral_analysis"]["multiplier"] - 18.8075) < 1e-9

    unresolved = json.loads(unresolved_path.read_text(encoding="utf-8"))
    assert any(item["topic"] == "spray_paint_periodic_ticks" for item in unresolved)
    assert any(item["topic"] == "skill_type_reference_region" for item in unresolved)
    off_tune_audit = json.loads(off_tune_audit_path.read_text(encoding="utf-8"))
    assert off_tune_audit["action_record_count"] == 43
    assert off_tune_audit["confirmed_source_backed_action_count"] == 37
    assert off_tune_audit["confirmed_selector_count"] == 5
    assert off_tune_audit["unresolved_action_ids"] == ["lynae_echo_hyvatia"]
    assert {
        "lynae_polychrome_leap_stage_1_c1",
        "lynae_visual_impact_c3",
        "lynae_resonance_liberation_prismatic_overblast_c5",
    }.issubset(set(off_tune_audit["internal_alias_action_ids"]))
    report = report_path.read_text(encoding="utf-8")
    assert "角色技能类型!2553:2635" in report
    assert "角色技能类型!772:784" not in report
    actions = json.loads((ROOT / "data/actions.json").read_text(encoding="utf-8"))
    missing = [
        item["id"]
        for item in actions
        if item.get("character_id") == "lynae"
        and float(item.get("damage_multiplier", 0.0) or 0.0) > 0.0
        and not item.get("source_status")
    ]
    assert not missing, missing
    print("lynae_excel_source_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
