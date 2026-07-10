from __future__ import annotations

import argparse
import json
import sys

from extract_aemeath_excel_data import (
    DEFAULT_ACTIONS,
    DEFAULT_CANDIDATES,
    DEFAULT_MAPPING,
    DEFAULT_OUTPUT,
    DEFAULT_REPORT,
    DEFAULT_REVIEW_REPORT,
    DEFAULT_TIMING_CANDIDATES,
    DEFAULT_TIMING_REPORT,
    DEFAULT_TIMING_UNRESOLVED,
    DEFAULT_UNMAPPED,
    DEFAULT_UNRESOLVED,
    SOURCE_DIR,
    extract,
    resolve_workbook_path,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def workbook_exists() -> bool:
    return SOURCE_DIR.exists() and any(SOURCE_DIR.glob("*.xlsx"))


def source_names(candidate: dict) -> list[str]:
    return [
        str(row.get("source_action_name") or "")
        for row in candidate.get("timing_candidate", {}).get("source_rows", [])
    ]


def main() -> int:
    if not workbook_exists():
        print(
            "SKIP: no Excel workbook was found in data/source. "
            "Place an Aemeath source workbook there to run the timing extraction smoke test."
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
        candidates=str(DEFAULT_CANDIDATES),
        coeff_resource_unresolved=str(DEFAULT_UNRESOLVED),
        review_report=str(DEFAULT_REVIEW_REPORT),
        timing_candidates=str(DEFAULT_TIMING_CANDIDATES),
        timing_unresolved=str(DEFAULT_TIMING_UNRESOLVED),
        timing_report=str(DEFAULT_TIMING_REPORT),
    )
    extract(args)

    assert DEFAULT_TIMING_CANDIDATES.exists(), f"Expected timing candidates at {DEFAULT_TIMING_CANDIDATES}"
    assert DEFAULT_TIMING_UNRESOLVED.exists(), f"Expected timing unresolved rows at {DEFAULT_TIMING_UNRESOLVED}"
    assert DEFAULT_TIMING_REPORT.exists(), f"Expected timing report at {DEFAULT_TIMING_REPORT}"

    report_text = DEFAULT_TIMING_REPORT.read_text(encoding="utf-8")
    for section in (
        "Heavy Attack Timing Candidates",
        "Form Switch Timing Candidates",
        "Sync Strike Timing Candidates",
        "Patch recommendation",
    ):
        assert section in report_text, f"Timing report should contain {section}"

    timing = json.loads(DEFAULT_TIMING_CANDIDATES.read_text(encoding="utf-8"))
    actions = timing.get("actions", [])
    assert actions, "Expected at least one timing candidate."

    for candidate in actions:
        action_id = candidate["action_id"]
        names = source_names(candidate)
        timing_candidate = candidate["timing_candidate"]

        if action_id.startswith("aemeath_form_switch"):
            assert not any("QTE" in name.upper() for name in names), (
                f"QTE rows must not be included in Form Switch candidate {action_id}"
            )
            assert not any(name.startswith("E2") for name in names), (
                f"E2 rows must not be included in Form Switch candidate {action_id}"
            )
            assert not any("强化E" in name or "凉뷴뙑E" in name for name in names), (
                f"Seraphic Duet rows must not be included in Form Switch candidate {action_id}"
            )
            assert all(name.startswith("E1") and "常规切换" in name for name in names), (
                f"Form Switch candidate {action_id} should use only normal E1 rows: {names}"
            )

        if action_id.startswith("aemeath_sync_strike"):
            assert not any("QTE" in name.upper() for name in names), (
                f"QTE rows must not be included in Sync Strike candidate {action_id}"
            )
            assert not any(name.startswith("E1") for name in names), (
                f"E1 rows must not be included in Sync Strike candidate {action_id}"
            )
            assert not any("强化E" in name or "凉뷴뙑E" in name for name in names), (
                f"Seraphic Duet rows must not be included in Sync Strike candidate {action_id}"
            )

        if action_id.startswith("aemeath_heavy") and timing_candidate.get("safe_to_patch"):
            has_charge_rows = bool(timing_candidate.get("charge_rows"))
            no_charge_reason = "source_clearly_no_charge_required" in timing_candidate.get("safe_to_patch_reasons", [])
            assert has_charge_rows or no_charge_reason, (
                f"Safe heavy candidate {action_id} must include charge rows or prove none are required."
            )
            if timing_candidate.get("instant_response_confidence") is None:
                assert timing_candidate.get("action_time_seconds", 0) >= 0.5, (
                    f"Safe heavy candidate {action_id} must not be suspiciously short."
                )
            max_hit_frame = timing_candidate.get("max_hit_frame")
            action_time_frames = timing_candidate.get("action_time_frames")
            if max_hit_frame is not None and action_time_frames is not None:
                assert action_time_frames >= max_hit_frame, (
                    f"Safe heavy candidate {action_id} action_time must be >= max hit frame."
                )

    sync_candidates = [candidate for candidate in actions if candidate["action_id"].startswith("aemeath_sync_strike")]
    if len(sync_candidates) >= 2:
        source_sets = {candidate["action_id"]: set(source_names(candidate)) for candidate in sync_candidates}
        assert len({frozenset(values) for values in source_sets.values()}) == len(source_sets), (
            f"Human and mech Sync Strike candidates should not share identical mixed source rows: {source_sets}"
        )

    print("Aemeath action timing extraction smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
