from __future__ import annotations

import argparse
import json
from pathlib import Path

from extract_aemeath_excel_data import (
    DEFAULT_ACTIONS,
    DEFAULT_MAPPING,
    DEFAULT_OUTPUT,
    DEFAULT_REPORT,
    DEFAULT_UNMAPPED,
    SOURCE_DIR,
    extract,
    resolve_workbook_path,
)


def workbook_exists() -> bool:
    return SOURCE_DIR.exists() and any(SOURCE_DIR.glob("*.xlsx"))


def main() -> int:
    if not workbook_exists():
        print(
            "SKIP: no Excel workbook was found in data/source. "
            "Place an Aemeath source workbook there to run the extraction smoke test."
        )
        return 0

    workbook_path = resolve_workbook_path(None)
    args = argparse.Namespace(
        workbook=str(workbook_path),
        actions=str(DEFAULT_ACTIONS),
        mapping=str(DEFAULT_MAPPING),
        output=str(DEFAULT_OUTPUT),
        unmapped=str(DEFAULT_UNMAPPED),
        report=str(DEFAULT_REPORT),
    )
    extract(args)

    assert DEFAULT_OUTPUT.exists(), f"Expected output JSON at {DEFAULT_OUTPUT}"
    assert DEFAULT_UNMAPPED.exists(), f"Expected unmapped JSON at {DEFAULT_UNMAPPED}"
    assert DEFAULT_REPORT.exists(), f"Expected report markdown at {DEFAULT_REPORT}"

    extracted = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    unmapped = json.loads(DEFAULT_UNMAPPED.read_text(encoding="utf-8"))
    current_actions = {
        action["id"]
        for action in json.loads(DEFAULT_ACTIONS.read_text(encoding="utf-8-sig"))
    }
    assert "actions" in extracted, "Output JSON must contain top-level actions"

    candidate_row_count = extracted.get("candidate_row_count", 0)
    mapped_action_count = len(extracted.get("actions", []))
    unmapped_row_count = len(unmapped.get("rows", []))
    assert candidate_row_count > 0, "Expected at least one Aemeath candidate row"
    assert mapped_action_count > 0, "Expected at least one mapped Aemeath action"
    assert candidate_row_count >= mapped_action_count + unmapped_row_count

    report_text = DEFAULT_REPORT.read_text(encoding="utf-8")
    for section in (
        "Workbook overview",
        "Extraction validation summary",
        "Base coefficient table",
        "Variant coefficient table",
        "Frame consistency table",
        "QTE exclusion summary",
        "Resource caution",
    ):
        assert section in report_text, f"Report should contain {section}"
    assert "Extracted relevant rows: 0" not in report_text, (
        "Report should not say zero extracted rows when a workbook exists"
    )

    actions = extracted["actions"]
    by_id = {action["action_id"]: action for action in actions}
    assert "aemeath_liberation_overdrive" in by_id, "Expected Overdrive extraction"
    assert "aemeath_heavenfall_finale" in by_id, "Expected Finale extraction"

    finale_base = by_id["aemeath_heavenfall_finale"].get("skill_data", {}).get("base", {})
    assert 17.8929 in finale_base.get("parsed_multipliers", []), (
        "Finale base numeric multiplier must stay 17.8929; numeric Excel cells are not percentages"
    )
    assert 0.178929 not in finale_base.get("parsed_multipliers", []), (
        "Finale base multiplier was divided by 100 unexpectedly"
    )

    validation = extracted.get("validation_summary", {})
    assert validation.get("frame_inconsistencies_remaining") == 0, (
        "Expected no remaining action_time < max_hit_frame inconsistencies"
    )
    assert validation.get("qte_rows_excluded", 0) > 0, "Expected QTE rows to be explicitly excluded"

    seraphic_ids = {"aemeath_seraphic_duet_overture", "aemeath_seraphic_duet_overturn", "aemeath_seraphic_duet_encore"}
    if seraphic_ids & current_actions:
        assert any(action["action_id"] in seraphic_ids for action in actions), "Expected Seraphic Duet extraction"

    liberation_pre_overdrive = "\u5927\u62db1-\u524d\u7f6e"
    liberation_pre_finale = "\u5927\u62db2-\u524d\u7f6e"
    category_words = [
        "\u666e\u653b",
        "\u91cd\u51fb",
        "\u5171\u9e23\u6280\u80fd",
        "\u5171\u9e23\u89e3\u653e",
        "\u4f24\u5bb3\u7c7b\u578b",
        "\u6280\u80fd\u7c7b\u578b",
    ]
    for action in actions:
        frame_data = action.get("frame_data", {})
        action_time_frames = frame_data.get("action_time_frames")
        max_hit_frame = frame_data.get("max_hit_frame")
        if action_time_frames is not None and max_hit_frame is not None:
            assert action_time_frames >= max_hit_frame, (
                f"{action['action_id']} action_time_frames is earlier than max_hit_frame"
            )

        for row in action.get("source_rows", []):
            source_name = row.get("source_action_name")
            assert not (
                source_name and "QTE" in source_name.upper() and action["action_id"].startswith("aemeath_form_switch")
            ), "QTE rows must not map to normal form switch actions"
            if source_name == liberation_pre_overdrive:
                assert action["action_id"] == "aemeath_liberation_overdrive", (
                    "大招1-前置 must map to Overdrive, not Seraphic Duet"
                )
            if source_name == liberation_pre_finale:
                assert action["action_id"] == "aemeath_heavenfall_finale", (
                    "大招2-前置 must map to Finale, not Seraphic Duet"
                )

        for coefficient_row in action.get("skill_data", {}).get("coefficient_rows", []):
            value = coefficient_row.get("raw_coefficients")
            if isinstance(value, str):
                assert not any(word in value for word in category_words), (
                    f"raw_coefficients should not be a damage category string: {value}"
                )

    qte_unmapped = [
        row for row in unmapped.get("rows", [])
        if row.get("mapping", {}).get("method") == "excluded_qte"
    ]
    assert qte_unmapped, "Expected QTE rows to be present in unmapped output with exclusion reasons"

    print("Aemeath Excel extraction smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
