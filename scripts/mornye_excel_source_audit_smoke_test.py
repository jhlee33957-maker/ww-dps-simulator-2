"""Smoke-test the source-evidence Mornye Excel audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"
REPORTS_DIR = PROJECT_ROOT / "reports"
WORKBOOK = DATA_DIR / "source" / "鸣潮动作数据汇总.xlsx"


def load_json(path: Path) -> dict:
    assert path.exists(), f"Missing expected audit artifact: {path}"
    assert path.stat().st_size > 0, f"Empty audit artifact: {path}"
    return json.loads(path.read_text(encoding="utf-8-sig"))


def assert_evidence(evidence: dict) -> None:
    assert evidence.get("sheet"), evidence
    assert isinstance(evidence.get("row"), int), evidence
    assert evidence.get("column"), evidence
    assert "raw_value" in evidence, evidence


def walk_evidence(value):
    if isinstance(value, dict):
        if {"sheet", "row", "column", "raw_value"}.issubset(value):
            yield value
        for child in value.values():
            yield from walk_evidence(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_evidence(child)


def main() -> None:
    assert WORKBOOK.exists() or (EXTRACTED_DIR / "mornye_raw_rows.json").exists()

    manifest = load_json(EXTRACTED_DIR / "mornye_excel_source_audit_manifest.json")
    row_index = load_json(EXTRACTED_DIR / "mornye_source_row_index.json")
    raw_rows = load_json(EXTRACTED_DIR / "mornye_raw_rows.json")
    resource = load_json(EXTRACTED_DIR / "mornye_resource_flow_audit.json")
    marker = load_json(EXTRACTED_DIR / "mornye_marker_tune_audit.json")
    diff = load_json(EXTRACTED_DIR / "mornye_source_vs_code_diff.json")
    actions = load_json(EXTRACTED_DIR / "mornye_excel_actions_source_audit.json")
    routes = load_json(EXTRACTED_DIR / "mornye_source_backed_cycle_candidates.json")

    assert row_index["source_rows"], "Expected Mornye source rows"
    assert raw_rows["rows"], "Expected raw Mornye/source context rows"
    assert (EXTRACTED_DIR / "mornye_raw_rows.csv").exists()
    assert (REPORTS_DIR / "mornye_source_vs_code_diff.md").exists()

    for claim in actions["claims"]:
        if claim.get("status") in {"source_confirmed", "source_partial", "source_conflict"}:
            evidence_items = list(walk_evidence(claim.get("evidence", [])))
            assert evidence_items, f"Claim lacks evidence: {claim.get('id')}"
            for item in evidence_items:
                assert_evidence(item)

    distributed = resource["questions"]["distributed_array"]
    assert distributed["verdict"] in {"source_confirmed", "source_partial", "source_ambiguous"}
    assert "classification" in distributed
    assert "15" in json.dumps(distributed, ensure_ascii=False)

    interfered = marker["interfered_marker"]
    assert interfered["application_condition_classification"] == "classified"
    assert interfered["current_implementation_verdict"] == "simplified_model_only"
    assert "谐度破坏" in json.dumps(interfered, ensure_ascii=False)

    comparisons = diff["comparisons"]
    comparison_text = json.dumps(comparisons, ensure_ascii=False)
    required_labels = [
        "mornye_basic_stage_1",
        "mornye_basic_stage_2",
        "mornye_basic_stage_3",
        "mornye_basic_stage_4",
        "mornye_heavy_geopotential_shift",
        "mornye_wfo_basic_stage_1",
        "mornye_wfo_basic_stage_2",
        "mornye_wfo_basic_stage_3",
        "mornye_skill_distributed_array",
        "mornye_heavy_inversion",
        "mornye_liberation_critical_protocol",
        "mornye_intro_convergence",
        "mornye_outro_recursion",
        "Syntony Field",
        "High Syntony Field",
        "谐度破坏",
        "震谐响应",
    ]
    for label in required_labels:
        assert label in comparison_text, f"Missing source/code diff entry for {label}"
    assert all(item.get("patch_recommendation") for item in comparisons), "Every diff row needs a recommendation"

    assert "under 10s" in json.dumps(routes, ensure_ascii=False) or "under_10" in json.dumps(routes, ensure_ascii=False)
    assert "not proven" in json.dumps(routes, ensure_ascii=False)

    assert manifest["hashes_before"] == manifest["hashes_after"], "Audit changed simulator mechanics/data files"

    print("mornye_excel_source_audit_smoke_test ok")


if __name__ == "__main__":
    main()
