from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    audit_path = ROOT / "data" / "extracted" / "aemeath_forte_circuit_source_audit.json"
    config_path = ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json"
    with audit_path.open("r", encoding="utf-8-sig") as file:
        audit = json.load(file)
    with config_path.open("r", encoding="utf-8-sig") as file:
        config = json.load(file)

    action_rows = {row["source_row"]: row for row in audit["action_rows"]}
    dmg_rows = {row["source_row"]: row for row in audit["dmg_rows"]}
    for row, repeat, interval in ((2786, 5, 4), (2787, 10, 2), (2931, 5, 4), (2932, 10, 2)):
        assert row in action_rows
        assert action_rows[row]["repeat_count"] == repeat
        assert action_rows[row]["hit_interval_frames"] == interval
        assert action_rows[row]["formula_type"] == "tune_response"
        assert action_rows[row]["source_status"] == "workbook_confirmed"

    for row in (2578, 2579, 2628, 2629):
        assert row in dmg_rows
        assert dmg_rows[row]["rate_lv_10"] == 10935
        assert dmg_rows[row]["multiplier"] == 1.0935
        assert dmg_rows[row]["damage_element_source_value"] == 2
        assert dmg_rows[row]["damage_type_source_value"] == 12
        assert dmg_rows[row]["related_property_source_value"] == 10000099
        assert dmg_rows[row]["damage_special_weakness_damage_ratio"] == 10000
        assert dmg_rows[row]["formula_type"] == "tune_response"
        assert dmg_rows[row]["source_status"] == "workbook_confirmed"

    followups = {
        entry["variant"]: entry
        for entry in config["modes"]["tune_rupture"]["seraphic_duet_followups"]
    }
    normal = followups["normal"]
    enhanced = followups["enhanced"]
    assert normal["id"] == "aemeath_seraphic_duet_tune_rupture_followup"
    assert normal["tune_multiplier"] == 1.0935
    assert normal["repeat_count"] == 5
    assert normal["hit_interval_frames"] == 4
    assert normal["formula_type"] == "tune_response"
    assert normal["source_status"] == "workbook_confirmed"
    assert set(normal["source_rows"]) == {2786, 2931, 2578, 2628}

    assert enhanced["id"] == "aemeath_seraphic_duet_tune_rupture_enhanced_followup"
    assert enhanced["tune_multiplier"] == 1.0935
    assert enhanced["repeat_count"] == 10
    assert enhanced["hit_interval_frames"] == 2
    assert enhanced["formula_type"] == "tune_response"
    assert enhanced["source_status"] == "workbook_confirmed"
    assert set(enhanced["source_rows"]) == {2787, 2932, 2579, 2629}

    unresolved_followups = [
        item
        for item in config["modes"]["tune_rupture"]["seraphic_duet_followups"]
        if item.get("source_status") == "unresolved_no_runtime_effect"
    ]
    assert unresolved_followups == []
    print("aemeath_forte_source_confirmed_followup_smoke_test ok")


if __name__ == "__main__":
    main()
