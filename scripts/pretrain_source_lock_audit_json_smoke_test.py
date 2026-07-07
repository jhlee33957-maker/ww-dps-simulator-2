from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_JSON = PROJECT_ROOT / "data" / "extracted" / "pretrain_aemeath_mornye_source_lock_audit.json"

NORMAL_LABEL = "\u5f3a\u5316E-\u9707\u8c10"
ENHANCED_LABEL = "\u5f3a\u5316E-\u9707\u8c10\u589e\u5e45"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def section_by_id(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {section["id"]: section for section in audit["sections"]}


def assert_no_unresolved_marker(value: Any, label: str) -> None:
    text = json.dumps(value, ensure_ascii=False)
    assert "unresolved_no_runtime_effect" not in text, f"{label} is still marked unresolved_no_runtime_effect"


def check_forte_followups(section: dict[str, Any]) -> None:
    followups = section["code_followups"]
    normal = followups["normal"]
    enhanced = followups["enhanced"]

    assert normal["label"] == NORMAL_LABEL
    assert normal["formula_type"] == "tune_response"
    assert normal["tune_multiplier"] == 1.0935
    assert normal["repeat_count"] == 5
    assert normal["source_status"] == "workbook_confirmed"
    assert_no_unresolved_marker(normal, NORMAL_LABEL)

    assert enhanced["label"] == ENHANCED_LABEL
    assert enhanced["formula_type"] == "tune_response"
    assert enhanced["tune_multiplier"] == 1.0935
    assert enhanced["repeat_count"] == 10
    assert enhanced["source_status"] == "workbook_confirmed"
    assert_no_unresolved_marker(enhanced, ENHANCED_LABEL)


def check_mornye_relative_momentum(section: dict[str, Any]) -> None:
    checks = {check["name"]: check for check in section["checks"]}
    expected = {
        "mornye_wfo_basic_stage_1 relative_momentum_delta": 10.0,
        "mornye_wfo_basic_stage_2 relative_momentum_delta": 12.0,
    }
    for check_name, value in expected.items():
        check = checks[check_name]
        assert check["ok"] is True
        assert check["expected"] == value
        assert check["actual"] == value
        assert_no_unresolved_marker(check, check_name)


def main() -> None:
    assert AUDIT_JSON.exists(), f"missing generated audit JSON: {AUDIT_JSON}"
    audit = load_json(AUDIT_JSON)

    assert audit["overall_status"] in {"PASS", "REVIEW_REQUIRED"}
    assert audit["source_confirmed_mismatches"] == []

    sections = section_by_id(audit)
    assert "aemeath_forte_followup" in sections
    assert "mornye_relative_momentum" in sections
    check_forte_followups(sections["aemeath_forte_followup"])
    check_mornye_relative_momentum(sections["mornye_relative_momentum"])
    print("pretrain_source_lock_audit_json_smoke_test ok")


if __name__ == "__main__":
    main()
