from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "generate_off_tune_value_mapping_audit.py"
AUDIT_PATH = ROOT / "data" / "extracted" / "off_tune_value_mapping_audit.json"
REPORT_PATH = ROOT / "reports" / "off_tune_value_mapping_audit.md"

DAMAGE_1_NOTE = (
    "Mornye Syntony Field Damage 1 deals damage but has a source-confirmed "
    "Off-Tune contribution of 0. Its repeated executions are supplied by the "
    "scheduled-effect engine."
)
DAMAGE_2_NOTE = (
    "Mornye Syntony Field Damage 2 is the non-QTE target-position deployment "
    "event and owns the source-confirmed Off-Tune contribution of 66.4."
)
LEGACY_NOTE_VARIANTS = {
    (
        "The payload deals damage but its source-confirmed Off-Tune contribution is zero. "
        "Its repeated executions are supplied by the scheduled-effect engine."
    ),
    (
        "The payload is the non-QTE target-position deployment event and carries the "
        "source-confirmed Off-Tune contribution."
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_audit() -> dict[str, Any]:
    raw = AUDIT_PATH.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    return json.loads(raw.decode("utf-8"))


def mapping_by_id(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["action_id"]: row for row in audit["mappings"]}


def syntony_free_audit(audit: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(audit, ensure_ascii=False))
    clone["mappings"] = [
        row
        for row in clone["mappings"]
        if row["action_id"] not in {"mornye_syntony_field_damage", "mornye_syntony_field_target_damage"}
    ]
    clone["notes"] = [
        note
        for note in clone.get("notes", [])
        if note not in {DAMAGE_1_NOTE, DAMAGE_2_NOTE} and note not in LEGACY_NOTE_VARIANTS
    ]
    return clone


def run_generator() -> None:
    subprocess.run([sys.executable, str(GENERATOR_PATH)], cwd=ROOT, check=True)


def main() -> None:
    original_audit_bytes = AUDIT_PATH.read_bytes()
    original_report_bytes = REPORT_PATH.read_bytes()
    original_audit = load_audit()
    original_unrelated = syntony_free_audit(original_audit)

    try:
        run_generator()
        first_json_hash = sha256(AUDIT_PATH)
        first_report_hash = sha256(REPORT_PATH)
        first_audit = load_audit()
        first_unrelated = syntony_free_audit(first_audit)

        run_generator()
        second_json_hash = sha256(AUDIT_PATH)
        second_report_hash = sha256(REPORT_PATH)
        second_audit = load_audit()
        second_report = REPORT_PATH.read_bytes().decode("utf-8")

        assert first_json_hash == second_json_hash
        assert first_report_hash == second_report_hash
        assert AUDIT_PATH.read_bytes() == original_audit_bytes
        assert REPORT_PATH.read_bytes() == original_report_bytes
        assert first_unrelated == original_unrelated
        assert syntony_free_audit(second_audit) == original_unrelated
        assert not REPORT_PATH.read_bytes().startswith(b"\xef\xbb\xbf")

        notes = second_audit.get("notes", [])
        assert notes.count(DAMAGE_1_NOTE) == 1
        assert notes.count(DAMAGE_2_NOTE) == 1
        for legacy_note in LEGACY_NOTE_VARIANTS:
            assert legacy_note not in notes
            assert legacy_note not in second_report

        rows = mapping_by_id(second_audit)
        damage_1 = rows["mornye_syntony_field_damage"]
        assert damage_1["off_tune_value"] == 0.0
        assert damage_1["source_status"] == "workbook_confirmed_zero_for_damage_1"
        assert damage_1["source_ref"] == "角色-女!4126"
        assert damage_1["damaging_action"] is True
        assert damage_1["policy_selectable"] is False
        assert damage_1["note"] == DAMAGE_1_NOTE

        damage_2 = rows["mornye_syntony_field_target_damage"]
        assert damage_2["off_tune_value"] == 66.4
        assert damage_2["source_status"] == "workbook_confirmed"
        assert damage_2["source_ref"] == "角色-女!4127"
        assert damage_2["damaging_action"] is True
        assert damage_2["policy_selectable"] is False
        assert damage_2["note"] == DAMAGE_2_NOTE

        assert second_report.count("`mornye_syntony_field_damage`") == 1
        assert second_report.count("`mornye_syntony_field_target_damage`") == 1
        assert second_report.count(DAMAGE_1_NOTE) == 1
        assert second_report.count(DAMAGE_2_NOTE) == 1
    finally:
        AUDIT_PATH.write_bytes(original_audit_bytes)
        REPORT_PATH.write_bytes(original_report_bytes)

    print("off_tune_audit_generator_idempotence_smoke_test ok")


if __name__ == "__main__":
    main()
