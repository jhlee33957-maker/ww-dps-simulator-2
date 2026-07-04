"""Smoke-test the read-only Mornye Excel audit extractor."""

from __future__ import annotations

import hashlib
import json
from argparse import Namespace
from pathlib import Path

from extract_mornye_excel_audit import (
    DEFAULT_SOURCE_DIR,
    MORNYE_SOURCE_NAME,
    PROJECT_ROOT,
    resolve_workbook_path,
    run_extraction,
)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    try:
        workbook = resolve_workbook_path(None)
    except FileNotFoundError:
        print(f"Skipping Mornye Excel audit smoke test: no workbook in {DEFAULT_SOURCE_DIR}")
        return

    actions_path = PROJECT_ROOT / "data" / "actions.json"
    before_hash = file_hash(actions_path)
    args = Namespace(
        workbook=workbook,
        actions=actions_path,
        output=PROJECT_ROOT / "data" / "extracted" / "mornye_excel_audit.json",
        candidates=PROJECT_ROOT / "data" / "extracted" / "mornye_source_alignment_candidates.json",
        unresolved=PROJECT_ROOT / "data" / "extracted" / "mornye_unresolved_rows.json",
        report=PROJECT_ROOT / "reports" / "mornye_excel_audit.md",
        review=PROJECT_ROOT / "reports" / "mornye_source_alignment_review.md",
    )
    result = run_extraction(args)
    after_hash = file_hash(actions_path)
    assert before_hash == after_hash, "Mornye Excel audit must not modify data/actions.json"

    for key in ("audit", "candidates", "unresolved", "report", "review"):
        output_path = Path(result[key])
        assert output_path.exists(), f"Missing expected audit artifact: {output_path}"
        assert output_path.stat().st_size > 0, f"Empty audit artifact: {output_path}"

    audit = json.loads(args.output.read_text(encoding="utf-8"))
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    unresolved = json.loads(args.unresolved.read_text(encoding="utf-8"))
    report = args.report.read_text(encoding="utf-8")
    review = args.review.read_text(encoding="utf-8")

    assert MORNYE_SOURCE_NAME in audit["source_name"]
    assert audit["audit_scope"]["read_only"] is True
    assert audit["source_row_count"] >= 40
    assert audit["action_comparisons"], "Expected action comparisons"
    assert any(item["action_id"] == "mornye_basic_stage_1" for item in audit["action_comparisons"])
    assert any(item["action_id"] == "mornye_outro_recursion" for item in audit["action_comparisons"])
    assert candidates["source_name"] == MORNYE_SOURCE_NAME
    assert isinstance(candidates["candidates"], list)
    assert unresolved, "Expected unresolved/review-only rows"
    assert "# Mornye Excel Audit" in report
    assert "## Action comparison table" in report
    assert "# Mornye Source Alignment Review" in review

    print("Mornye Excel audit smoke test passed")


if __name__ == "__main__":
    main()
