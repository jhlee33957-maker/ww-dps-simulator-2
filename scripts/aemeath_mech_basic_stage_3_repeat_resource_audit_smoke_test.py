from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "aemeath_mech_basic_stage_3_repeat_resource_audit.md"
JSON_PATH = ROOT / "data" / "extracted" / "aemeath_mech_basic_stage_3_repeat_resource_audit.json"


def assert_close(actual: float, expected: float, label: str) -> None:
    assert math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    assert REPORT_PATH.exists(), f"Missing report: {REPORT_PATH}"
    assert JSON_PATH.exists(), f"Missing JSON report: {JSON_PATH}"

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    assert data["action_id"] == "aemeath_mech_basic_stage_3"
    assert data["repeat_row"] == "角色-女!2890"
    assert data["repeat_source_ref"] == "角色-女!D2890"
    assert data["repeat_count"] == 3
    assert_close(data["off_tune_simple_sum"], 58.06, "simple Off-Tune")
    assert_close(data["off_tune_repeat_aware"], 62.54, "repeat-aware Off-Tune")
    assert_close(data["current_off_tune_before_patch"], 58.06, "pre-patch Off-Tune")
    assert_close(data["corrected_off_tune_after_patch"], 62.54, "post-patch Off-Tune")
    assert_close(data["raw_resonance_energy_repeat_aware"], 1.96, "raw resonance energy")
    assert_close(data["raw_concerto_energy_repeat_aware"], 3.91, "raw concerto energy")
    assert_close(data["raw_core_resource_repeat_aware"], 18.54, "raw core resource")
    assert data["current_simulator_resonance_energy_gain"] == 7
    assert data["current_simulator_concerto_energy_gain"] == 6
    assert_close(data["current_simulator_sync_delta"], 18.54, "simulator sync delta")
    assert data["resource_unit_status"] == "simulator_resource_units_not_direct_excel_raw_values"
    assert data["resource_numeric_changes_this_patch"] is False
    assert "62.54" in report_text
    assert "resonance_energy_gain" in report_text
    assert "concerto_energy_gain" in report_text
    assert "not changed" in report_text

    print("aemeath_mech_basic_stage_3_repeat_resource_audit_smoke_test ok")


if __name__ == "__main__":
    main()
