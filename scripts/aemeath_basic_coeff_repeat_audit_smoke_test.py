from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "aemeath_basic_coefficient_repeat_audit.md"
JSON_PATH = ROOT / "data" / "extracted" / "aemeath_basic_coefficient_repeat_audit.json"


def main() -> None:
    assert REPORT_PATH.exists(), f"Missing report: {REPORT_PATH}"
    assert JSON_PATH.exists(), f"Missing JSON report: {JSON_PATH}"
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert data["target_action_id"] == "aemeath_mech_basic_stage_3"
    assert math.isclose(data["old_total"], 1.6653, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(data["corrected_total"], 1.0875, rel_tol=1e-9, abs_tol=1e-9)
    assert data["removed_unsupported_hits"][0]["damage_multiplier"] == 0.6165
    assert data["nearby_basic_action_audit"], "Nearby basic action audit should be recorded."
    assert "aemeath_mech_basic_stage_4" in {
        item["action_id"] for item in data["nearby_basic_action_audit"]
    }
    issues = {item["field"]: item for item in data["off_tune_resource_repeat_issues"]}
    assert issues, "Expected explicit repeat-resource/off-tune records."
    off_tune_issue = issues["off_tune_value"]
    assert off_tune_issue["status"] == "corrected_to_repeat_aware"
    assert math.isclose(off_tune_issue["current_value"], 62.54, rel_tol=1e-9, abs_tol=1e-9)
    assert issues["resonance_energy_gain"]["status"] == "unresolved_not_changed"
    assert issues["resonance_energy_gain"]["raw_workbook_repeat_aware"] == 1.96
    assert issues["concerto_energy_gain"]["status"] == "unresolved_not_changed"
    assert issues["concerto_energy_gain"]["raw_workbook_repeat_aware"] == 3.91
    assert "old implemented hit multipliers" in report_text.lower()
    assert "corrected hit multipliers" in report_text.lower()
    assert "62.54" in report_text
    print("aemeath_basic_coeff_repeat_audit_smoke_test ok")


if __name__ == "__main__":
    main()
