from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TARGET_ACTIONS = {
    "aemeath_form_switch_to_mech_normal",
    "aemeath_form_switch_to_aemeath_normal",
    "aemeath_form_switch_to_aemeath_after_overdrive",
    "aemeath_seraphic_duet_encore",
}
ROLE_FEMALE_SHEET = "\u89d2\u8272-\u5973"
DAMAGE_1_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4126"
DAMAGE_2_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4127"
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
ZERO_VALUE_ALLOWED_STATUSES = {
    "not_found_or_non_damaging",
    "non_damaging_selector",
    "workbook_confirmed_tune_break_rows_zero",
    "workbook_confirmed_zero_for_damage_1",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def has_normal_damage(action: dict[str, Any]) -> bool:
    if action.get("action_type") == "tune_break":
        return False
    if action.get("character_id") not in {"aemeath", "mornye"}:
        return False
    for hit in action.get("hits") or []:
        if str(hit.get("damage_category", "normal")) == "normal" and float(hit.get("damage_multiplier") or 0.0) > 0.0:
            return True
    return float(action.get("damage_multiplier") or 0.0) > 0.0


def has_transition_damage(record: dict[str, Any]) -> bool:
    return record.get("character_id") in {"aemeath", "mornye"} and bool(record.get("hits"))


def assert_metadata(action: dict[str, Any], unresolved_ids: set[str]) -> None:
    action_id = action["id"]
    source_status = action.get("off_tune_value_source_status")
    value = action.get("off_tune_value")
    assert source_status, f"{action_id} is missing off_tune_value_source_status"
    if source_status == "unresolved_missing_excel_mapping":
        assert action_id in unresolved_ids, f"{action_id} unresolved but not listed in audit"
        return
    assert value is not None, f"{action_id} has silent null off_tune_value"
    if float(value) == 0.0:
        assert source_status in ZERO_VALUE_ALLOWED_STATUSES, (
            f"{action_id} has zero Off-Tune without explanatory status: {source_status}"
        )


def main() -> None:
    actions = read_json(ROOT / "data" / "actions.json")
    transition_actions = read_json(ROOT / "data" / "transition_actions.json")
    audit = read_json(ROOT / "data" / "extracted" / "off_tune_value_mapping_audit.json")
    report = (ROOT / "reports" / "off_tune_value_mapping_audit.md").read_text(encoding="utf-8")

    unresolved_ids = set(audit["unresolved_damaging_action_ids"])
    damaging_action_ids: list[str] = []
    for action in actions:
        if has_normal_damage(action):
            damaging_action_ids.append(action["id"])
            assert_metadata(action, unresolved_ids)
    for record in transition_actions:
        if has_transition_damage(record):
            damaging_action_ids.append(record["id"])
            assert_metadata(record, unresolved_ids)

    assert TARGET_ACTIONS.issubset(set(damaging_action_ids))
    assert set(audit["damaging_actions_checked"]) == set(damaging_action_ids)
    assert set(audit["actions_with_missing_off_tune_metadata_before_patch"]) == TARGET_ACTIONS
    assert audit["actions_with_missing_off_tune_metadata_after_patch"] == []
    assert audit["off_tune_mapping_completeness_status"] == "complete"
    assert audit["unresolved_damaging_action_ids"] == []
    notes = audit.get("notes", [])
    assert notes.count(DAMAGE_1_NOTE) == 1
    assert notes.count(DAMAGE_2_NOTE) == 1
    for legacy_note in LEGACY_NOTE_VARIANTS:
        assert legacy_note not in notes
        assert legacy_note not in report

    actions_by_id = {action["id"]: action for action in actions}
    assert actions_by_id["aemeath_form_switch_to_mech_normal"]["off_tune_value_alias_of"] == "aemeath_mech_basic_stage_1"
    assert actions_by_id["aemeath_form_switch_to_aemeath_normal"]["off_tune_value_alias_of"] == "aemeath_basic_form_stage_1"
    assert (
        actions_by_id["aemeath_form_switch_to_aemeath_after_overdrive"]["off_tune_value_alias_of"]
        == "aemeath_basic_form_stage_2"
    )
    assert actions_by_id["aemeath_seraphic_duet_encore"]["off_tune_value"] == 128.0
    assert actions_by_id["aemeath_seraphic_duet_encore"]["off_tune_value_source_ref"] == "角色-女!S2925:S2929"

    damage_1 = actions_by_id["mornye_syntony_field_damage"]
    assert damage_1["off_tune_value"] == 0.0
    assert damage_1["off_tune_value_source_status"] == "workbook_confirmed_zero_for_damage_1"
    assert DAMAGE_1_ACTION_REF in damage_1["off_tune_value_source_ref"]
    assert damage_1["id"] not in unresolved_ids

    damage_2 = actions_by_id["mornye_syntony_field_target_damage"]
    assert damage_2["off_tune_value"] == 66.4
    assert damage_2["off_tune_value_source_status"] == "workbook_confirmed"
    assert DAMAGE_2_ACTION_REF in damage_2["off_tune_value_source_ref"]
    assert damage_2["id"] in damaging_action_ids
    assert damage_2["id"] not in unresolved_ids

    mappings_by_id = {row["action_id"]: row for row in audit["mappings"]}
    assert mappings_by_id["mornye_syntony_field_damage"]["note"] == DAMAGE_1_NOTE
    assert mappings_by_id["mornye_syntony_field_target_damage"]["note"] == DAMAGE_2_NOTE
    assert report.count("`mornye_syntony_field_damage`") == 1
    assert report.count("`mornye_syntony_field_target_damage`") == 1
    assert report.count(DAMAGE_1_NOTE) == 1
    assert report.count(DAMAGE_2_NOTE) == 1

    for action_id in TARGET_ACTIONS:
        assert action_id in report

    print("off_tune_damaging_action_metadata_guard_smoke_test ok")


if __name__ == "__main__":
    main()
