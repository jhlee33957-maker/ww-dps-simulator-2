from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "pretrain_aemeath_mornye_source_lock_audit.py"
AUDIT_JSON = PROJECT_ROOT / "data" / "extracted" / "pretrain_aemeath_mornye_source_lock_audit.json"
AUDIT_REPORT = PROJECT_ROOT / "reports" / "pretrain_aemeath_mornye_source_lock_audit.md"

PASS_SECTIONS = {
    "aemeath_forte_followup",
    "aemeath_overdrive_forte_state",
    "aemeath_mech_basic_stage_3_repeat_aware",
    "aemeath_tune_break_starburst",
    "mornye_relative_momentum",
    "mornye_interfered_marker",
    "mornye_tune_break_particle_jet",
}
REVIEW_ALLOWED_SECTIONS = {
    "mornye_baseline_rest_mass",
    "mornye_geopotential_syntony",
    "mornye_high_syntony_critical_protocol",
}
NON_WORKBOOK_SOURCE_IDS = {
    "aemeath:aemeath_user_real_01",
    "mornye:mornye_user_real_01",
    "starfield_calibrator",
    "everbright_polestar",
    "mornye_halo_of_starry_radiance_5set",
    "aemeath_trailblazing_star_5set",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    try:
        result = subprocess.run(
            [sys.executable, str(AUDIT_SCRIPT)],
            cwd=PROJECT_ROOT,
            timeout=180,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            "pretrain source-lock audit did not exit within 180 seconds\n"
            f"stdout:\n{exc.stdout or ''}\n"
            f"stderr:\n{exc.stderr or ''}"
        ) from exc
    if result.returncode != 0:
        raise AssertionError(
            "pretrain source-lock audit failed\n"
            f"returncode={result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    assert "pretrain_aemeath_mornye_source_lock_audit" in result.stdout

    assert AUDIT_JSON.exists(), f"missing generated audit JSON: {AUDIT_JSON}"
    assert AUDIT_REPORT.exists(), f"missing generated audit report: {AUDIT_REPORT}"
    audit = load_json(AUDIT_JSON)

    assert audit["overall_status"] in {"PASS", "REVIEW_REQUIRED"}
    assert audit["source_confirmed_mismatches"] == []
    assert audit["workbook_rows_checked"], "audit should list workbook rows checked"

    sections = {section["id"]: section for section in audit["sections"]}
    for section_id in PASS_SECTIONS:
        assert sections[section_id]["status"] == "PASS", sections[section_id]
        assert sections[section_id]["mismatches"] == []

    for section_id in REVIEW_ALLOWED_SECTIONS:
        assert sections[section_id]["status"] == "REVIEW_REQUIRED", sections[section_id]
        assert sections[section_id]["mismatches"] == []
        assert sections[section_id]["review_required"], f"{section_id} should explain the review item"

    non_workbook_sources = audit["non_workbook_sources"]
    found_non_workbook_ids = {item["id"] for item in non_workbook_sources}
    missing = NON_WORKBOOK_SOURCE_IDS - found_non_workbook_ids
    assert not missing, f"missing non-workbook sources: {sorted(missing)}"

    for item in non_workbook_sources:
        text = json.dumps(item, ensure_ascii=False).lower()
        assert "workbook_confirmed" not in text, f"non-workbook source is marked workbook-confirmed: {item}"

    report_text = AUDIT_REPORT.read_text(encoding="utf-8")
    assert "# Pretrain Aemeath / Mornye Source-lock Audit" in report_text
    assert "## Mismatches" in report_text
    assert "- None." in report_text
    print("pretrain_aemeath_mornye_source_lock_audit_smoke_test ok")


if __name__ == "__main__":
    main()
