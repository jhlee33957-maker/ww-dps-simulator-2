from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_audit_outputs_exist_and_confirm_tune_rupture_followup() -> None:
    audit_path = ROOT / "data" / "extracted" / "aemeath_forte_circuit_source_audit.json"
    report_path = ROOT / "reports" / "aemeath_forte_circuit_source_audit.md"
    assert audit_path.exists(), f"missing audit json: {audit_path}"
    assert report_path.exists(), f"missing audit report: {report_path}"

    with audit_path.open("r", encoding="utf-8-sig") as file:
        audit = json.load(file)
    summary = audit["summary"]
    assert summary["runtime_damage_status"] == "workbook_confirmed"
    assert summary["formula_type"] == "tune_response"
    assert summary["source_confirmed_action_rows"] == [2786, 2787, 2931, 2932]
    assert summary["source_confirmed_dmg_rows"] == [2578, 2579, 2628, 2629]
    assert summary["multiplier"] == 1.0935
    assert summary["normal_repeat_count"] == 5
    assert summary["enhanced_repeat_count"] == 10

    rows = {
        int(row["source_row"])
        for section in ("action_rows", "dmg_rows")
        for row in audit.get(section, [])
    }
    for expected in (2786, 2787, 2931, 2932, 2578, 2579, 2628, 2629):
        assert expected in rows, f"missing source-confirmed row {expected}"
    assert all(row["source_status"] == "workbook_confirmed" for row in audit["action_rows"])
    assert all(row["source_status"] == "workbook_confirmed" for row in audit["dmg_rows"])

    text = report_path.read_text(encoding="utf-8-sig").lower()
    assert "workbook_confirmed" in text
    assert "1.0935" in text


def main() -> None:
    test_audit_outputs_exist_and_confirm_tune_rupture_followup()
    print("aemeath_forte_circuit_source_audit_smoke_test ok")


if __name__ == "__main__":
    main()
