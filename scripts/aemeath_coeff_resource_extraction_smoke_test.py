from __future__ import annotations

import argparse
import json

from extract_aemeath_excel_data import (
    DEFAULT_ACTIONS,
    DEFAULT_CANDIDATES,
    DEFAULT_MAPPING,
    DEFAULT_OUTPUT,
    DEFAULT_REPORT,
    DEFAULT_REVIEW_REPORT,
    DEFAULT_UNMAPPED,
    DEFAULT_UNRESOLVED,
    SOURCE_DIR,
    extract,
    resolve_workbook_path,
)


def workbook_exists() -> bool:
    return SOURCE_DIR.exists() and any(SOURCE_DIR.glob("*.xlsx"))


def candidate_by_id(candidates: dict) -> dict[str, dict]:
    return {action["action_id"]: action for action in candidates.get("actions", [])}


def row_names(candidate: dict) -> set[str]:
    return {
        str(row.get("source_action_name") or "")
        for row in candidate.get("coefficient_candidate", {}).get("base_source_rows", [])
    }


def main() -> int:
    if not workbook_exists():
        print(
            "SKIP: no Excel workbook was found in data/source. "
            "Place an Aemeath source workbook there to run the coefficient/resource extraction smoke test."
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
    )
    extract(args)

    for path in (DEFAULT_OUTPUT, DEFAULT_CANDIDATES, DEFAULT_UNRESOLVED, DEFAULT_REVIEW_REPORT, DEFAULT_REPORT):
        assert path.exists(), f"Expected extraction artifact at {path}"

    candidates = json.loads(DEFAULT_CANDIDATES.read_text(encoding="utf-8"))
    unresolved = json.loads(DEFAULT_UNRESOLVED.read_text(encoding="utf-8"))
    current_actions = {
        action["id"]: action
        for action in json.loads(DEFAULT_ACTIONS.read_text(encoding="utf-8-sig"))
    }
    by_id = candidate_by_id(candidates)

    finale = by_id.get("aemeath_heavenfall_finale", {}).get("coefficient_candidate", {})
    assert 17.8929 in finale.get("parsed_multipliers", []), (
        "Finale candidate must preserve 17.8929 as an already-normalized Excel decimal."
    )
    assert 0.178929 not in finale.get("parsed_multipliers", []), (
        "Finale candidate must not divide numeric Excel decimals by 100."
    )
    finale_comparison = finale.get("current_actions_comparison", {})
    if finale_comparison.get("current_hit_count") == 1 and finale_comparison.get("candidate_hit_count") == 1:
        assert finale_comparison.get("shape_status") == "exact_match", "Finale one-hit candidate should match current shape."

    damage_category_tokens = [
        "\u4f24\u5bb3",
        "\u4f24\u5bb3\u7c7b\u578b",
        "\u6280\u80fd\u7c7b\u578b",
        "\u666e\u653b",
        "\u91cd\u51fb",
        "\u5171\u9e23\u6280\u80fd",
        "\u5171\u9e23\u89e3\u653e",
    ]
    for action in candidates.get("actions", []):
        coeff = action.get("coefficient_candidate", {})
        for value in coeff.get("raw_coefficients", []):
            if isinstance(value, str):
                assert not any(token in value for token in damage_category_tokens), (
                    f"{action['action_id']} base raw coefficient contains category text: {value}"
                )

        if coeff.get("safe_to_patch"):
            critical = [
                warning
                for warning in coeff.get("warnings", [])
                if warning.get("severity") == "critical"
            ]
            assert not critical, f"{action['action_id']} safe_to_patch has critical warnings: {critical}"
            assert not coeff.get("safe_to_patch_reasons"), (
                f"{action['action_id']} safe_to_patch should not have blocking reasons: {coeff.get('safe_to_patch_reasons')}"
            )

        comparison = coeff.get("current_actions_comparison", {})
        current_hit_count = comparison.get("current_hit_count", 0)
        candidate_hit_count = comparison.get("candidate_hit_count", 0)
        if current_hit_count > candidate_hit_count:
            assert not coeff.get("safe_to_patch"), (
                f"{action['action_id']} compressed candidate must not be safe_to_patch"
            )
            assert "candidate_shorter_than_current" in coeff.get("safe_to_patch_reasons", []), (
                f"{action['action_id']} should explain that candidate is shorter than current"
            )

    normal_form_switch_ids = {
        "aemeath_form_switch_to_mech",
        "aemeath_form_switch_to_aemeath",
        "aemeath_form_switch_to_mech_normal",
        "aemeath_form_switch_to_aemeath_normal",
        "aemeath_sync_strike_to_mech",
        "aemeath_sync_strike_to_aemeath",
        "aemeath_sync_strike_armament_merge",
        "aemeath_sync_strike_call_of_dawn",
    }
    for action_id in normal_form_switch_ids:
        candidate = by_id.get(action_id)
        if not candidate:
            continue
        assert not any("QTE" in name.upper() for name in row_names(candidate)), (
            f"QTE rows must not be included in normal form-switch coefficient candidates for {action_id}"
        )

    sequence_rows = [
        row
        for row in unresolved.get("rows", [])
        if row.get("reason") == "sequence_variant"
    ]
    assert sequence_rows, "Expected C2/C3/sequence rows to be excluded from base candidates."
    for action in candidates.get("actions", []):
        for name in row_names(action):
            assert not any(token in name.upper() for token in ("C1", "C2", "C3", "C4", "C5", "C6")), (
                f"Sequence row {name} was included in {action['action_id']} base candidate."
            )

    basic_stage_candidates = [
        by_id.get("aemeath_basic_form_stage_3", {}),
        by_id.get("aemeath_basic_form_stage_4", {}),
        by_id.get("aemeath_mech_basic_stage_3", {}),
    ]
    for candidate in basic_stage_candidates:
        if not candidate:
            continue
        for name in row_names(candidate):
            assert not name.upper().endswith("D"), (
                f"Dodge/counter row {name} was included in {candidate['action_id']} base candidate."
            )
    assert any(row.get("reason") == "dodge_counter" for row in unresolved.get("rows", [])), (
        "Expected dodge/counter rows such as A3-1D to be excluded from base candidates."
    )

    def assert_complete_or_unsafe(action_id: str, current_hits: int, compressed_values: list[float] | None = None) -> None:
        candidate = by_id.get(action_id, {}).get("coefficient_candidate", {})
        if not candidate:
            return
        comparison = candidate.get("current_actions_comparison", {})
        if comparison.get("current_hit_count") == current_hits:
            assert comparison.get("candidate_hit_count") == current_hits or not candidate.get("safe_to_patch"), (
                f"{action_id} must either reconstruct {current_hits} hits or be unsafe"
            )
        if compressed_values is not None and candidate.get("parsed_multipliers") == compressed_values:
            assert not candidate.get("safe_to_patch"), f"{action_id} compressed candidate must not be safe"

    assert_complete_or_unsafe("aemeath_mech_basic_stage_1", 3, [0.232])
    assert_complete_or_unsafe("aemeath_basic_form_stage_4", 6, [0.0673, 0.0673, 1.0094])
    assert_complete_or_unsafe("aemeath_liberation_overdrive", 4, [2.008, 2.6774])
    assert_complete_or_unsafe("aemeath_seraphic_duet_overturn", 13, [0.179, 0.1492, 0.2386, 0.5965])
    assert_complete_or_unsafe("aemeath_seraphic_duet_encore", 8)
    assert_complete_or_unsafe("aemeath_heavy_aemeath_charged_1", 2, [0.1857])

    for action_id in (
        "aemeath_mech_basic_stage_1",
        "aemeath_basic_form_stage_4",
        "aemeath_liberation_overdrive",
        "aemeath_seraphic_duet_overturn",
        "aemeath_seraphic_duet_encore",
        "aemeath_heavy_aemeath_charged_1",
    ):
        if action_id not in current_actions or action_id not in by_id:
            continue
        current_count = len([hit for hit in current_actions[action_id].get("hits", []) if hit.get("damage_multiplier") not in (None, 0)])
        candidate = by_id[action_id]["coefficient_candidate"]
        comparison = candidate.get("current_actions_comparison", {})
        if comparison.get("candidate_hit_count", 0) < current_count:
            assert comparison.get("shape_status") == "shorter_than_current"
            assert not candidate.get("safe_to_patch")

    report_text = DEFAULT_REVIEW_REPORT.read_text(encoding="utf-8")
    for section in (
        "## Summary",
        "## Multihit reconstruction summary",
        "## Candidate vs current shape table",
        "## Expanded coefficient segments",
        "## Critical warnings",
        "## Safe-to-patch table",
        "## Coefficient candidate table",
        "## Resource candidate table",
        "## Excluded / unresolved rows",
        "## Current actions.json comparison",
    ):
        assert section in report_text, f"Review report should contain {section}"

    print("Aemeath coefficient/resource extraction smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
