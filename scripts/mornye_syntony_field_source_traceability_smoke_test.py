from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ROLE_FEMALE_SHEET = "\u89d2\u8272-\u5973"
SKILL_TYPE_SHEET = "\u89d2\u8272\u6280\u80fd\u7c7b\u578b"

assert [ord(c) for c in ROLE_FEMALE_SHEET] == [0x89D2, 0x8272, 0x002D, 0x5973]
assert [ord(c) for c in SKILL_TYPE_SHEET] == [0x89D2, 0x8272, 0x6280, 0x80FD, 0x7C7B, 0x578B]

DAMAGE_1_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4126"
DAMAGE_2_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4127"
DAMAGE_1_SKILL_REF = f"dmg/{SKILL_TYPE_SHEET}!2655"
DAMAGE_2_SKILL_REF = f"dmg/{SKILL_TYPE_SHEET}!2656"
DAMAGE_1_COMBINED_REF = f"{DAMAGE_1_ACTION_REF} / {DAMAGE_1_SKILL_REF}"
DAMAGE_2_COMBINED_REF = f"{DAMAGE_2_ACTION_REF} / {DAMAGE_2_SKILL_REF}"

RELEVANT_TEXT_FILES = [
    ROOT / "data" / "actions.json",
    ROOT / "simulator" / "simulation.py",
    ROOT / "direct_action_data_patch_manifest_v61.json",
    ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json",
    ROOT / "scripts" / "generate_off_tune_value_mapping_audit.py",
    ROOT / "data" / "extracted" / "off_tune_value_mapping_audit.json",
    ROOT / "reports" / "off_tune_value_mapping_audit.md",
    ROOT / "reports" / "mornye_syntony_field_scheduler_audit.md",
    ROOT / "scripts" / "mornye_syntony_field_source_traceability_smoke_test.py",
    ROOT / "scripts" / "mornye_syntony_field_payload_data_smoke_test.py",
    ROOT / "scripts" / "off_tune_damaging_action_metadata_guard_smoke_test.py",
    ROOT / "scripts" / "off_tune_value_mapping_audit_smoke_test.py",
    ROOT / "PROJECT_PROGRESS_STATE.json",
]

JSON_FILES = [
    ROOT / "data" / "actions.json",
    ROOT / "direct_action_data_patch_manifest_v61.json",
    ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json",
    ROOT / "data" / "extracted" / "off_tune_value_mapping_audit.json",
    ROOT / "PROJECT_PROGRESS_STATE.json",
]

CORRUPTED_MARKERS = (
    "\uc695\ub000",
    "\u963f?",
    "?\ubc34\ub3e8",
    "\ufffd",
    chr(0x9C32),
    "\uc37c\uad73",
)


def read_json(path: Path):
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf"), f"{path} has BOM"
    return json.loads(data.decode("utf-8"))


def assert_no_corrupted_markers() -> None:
    for path in RELEVANT_TEXT_FILES:
        data = path.read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf"), f"{path} has BOM"
        text = data.decode("utf-8")
        for marker in CORRUPTED_MARKERS:
            assert marker not in text, f"{path} still contains corrupted source marker {marker!r}"


def main() -> None:
    assert_no_corrupted_markers()
    for path in JSON_FILES:
        read_json(path)

    actions = {item["id"]: item for item in read_json(ROOT / "data" / "actions.json")}
    damage_1 = actions["mornye_syntony_field_damage"]
    damage_2 = actions["mornye_syntony_field_target_damage"]

    assert damage_1["off_tune_value_source_ref"] == DAMAGE_1_COMBINED_REF
    assert damage_1["mechanic_effects"]["source_ref"] == DAMAGE_1_COMBINED_REF
    assert damage_1["off_tune_value"] == 0.0
    assert damage_1["off_tune_value_source_status"] == "workbook_confirmed_zero_for_damage_1"
    assert damage_2["off_tune_value_source_ref"] == DAMAGE_2_COMBINED_REF
    assert damage_2["mechanic_effects"]["source_ref"] == DAMAGE_2_COMBINED_REF
    assert damage_2["off_tune_value"] == 66.4
    assert damage_2["off_tune_value_source_status"] == "workbook_confirmed"
    assert DAMAGE_2_ACTION_REF not in damage_1["off_tune_value_source_ref"]
    assert DAMAGE_1_ACTION_REF not in damage_2["off_tune_value_source_ref"]

    root_manifest = read_json(ROOT / "direct_action_data_patch_manifest_v61.json")
    source_manifest = read_json(ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json")
    assert root_manifest == source_manifest
    root_manifest_text = (ROOT / "direct_action_data_patch_manifest_v61.json").read_text(encoding="utf-8")
    source_manifest_text = (ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json").read_text(
        encoding="utf-8"
    )
    for source_ref in (DAMAGE_1_ACTION_REF, DAMAGE_2_ACTION_REF, DAMAGE_1_SKILL_REF, DAMAGE_2_SKILL_REF):
        assert source_ref in root_manifest_text
        assert source_ref in source_manifest_text

    report = (ROOT / "reports" / "mornye_syntony_field_scheduler_audit.md").read_text(encoding="utf-8")
    for source_ref in (
        f"{ROLE_FEMALE_SHEET}!4117",
        f"{ROLE_FEMALE_SHEET}!4118",
        f"{ROLE_FEMALE_SHEET}!4125",
        DAMAGE_1_ACTION_REF,
        DAMAGE_2_ACTION_REF,
        DAMAGE_1_SKILL_REF,
        DAMAGE_2_SKILL_REF,
    ):
        assert source_ref in report

    audit = read_json(ROOT / "data" / "extracted" / "off_tune_value_mapping_audit.json")
    mappings = {row["action_id"]: row for row in audit["mappings"]}
    assert mappings["mornye_syntony_field_damage"]["source_ref"] == DAMAGE_1_ACTION_REF
    assert mappings["mornye_syntony_field_damage"]["off_tune_value"] == 0.0
    assert mappings["mornye_syntony_field_damage"]["source_status"] == "workbook_confirmed_zero_for_damage_1"
    assert mappings["mornye_syntony_field_target_damage"]["source_ref"] == DAMAGE_2_ACTION_REF
    assert mappings["mornye_syntony_field_target_damage"]["off_tune_value"] == 66.4
    assert mappings["mornye_syntony_field_target_damage"]["source_status"] == "workbook_confirmed"

    print("mornye_syntony_field_source_traceability_smoke_test ok")


if __name__ == "__main__":
    main()
