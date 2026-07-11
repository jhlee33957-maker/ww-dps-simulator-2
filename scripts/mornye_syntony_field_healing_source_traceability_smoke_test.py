from __future__ import annotations

import json
from pathlib import Path

from mornye_syntony_field_heal_test_helpers import DATA_DIR, NORMAL_FRAMES


ROOT = Path(__file__).resolve().parents[1]
ROLE_FEMALE_SHEET = "\u89d2\u8272-\u5973"
SKILL_TYPE_SHEET = "\u89d2\u8272\u6280\u80fd\u7c7b\u578b"
NORMAL_FIELD_REF = f"{ROLE_FEMALE_SHEET}!4118"
HIGH_FIELD_REF = f"{ROLE_FEMALE_SHEET}!4119"
NORMAL_HEAL_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4120"
HIGH_HEAL_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4121"
HEAL_SKILL_REF = f"{SKILL_TYPE_SHEET}!533"
NORMAL_HEAL_COMBINED_REF = f"{NORMAL_HEAL_ACTION_REF} / {HEAL_SKILL_REF}"
HIGH_HEAL_COMBINED_REF = f"{HIGH_HEAL_ACTION_REF} / {HEAL_SKILL_REF}"
BAD_HEALING_SOURCE_MARKERS = [
    chr(0x6B32) + chr(0xB000) + chr(0x3F) + chr(0x3F) + chr(0x3F),
    chr(0x963F) + chr(0x3F),
    chr(0x3F) + chr(0xBC34) + chr(0xB3A8),
    chr(0xFFFD),
]


RELEVANT_FILES = [
    ROOT / "data" / "actions.json",
    ROOT / "data" / "transition_actions.json",
    ROOT / "simulator" / "simulation.py",
    ROOT / "direct_action_data_patch_manifest_v61.json",
    ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json",
    ROOT / "reports" / "mornye_syntony_field_healing_scheduler_audit.md",
    ROOT / "scripts" / "mornye_syntony_field_heal_payload_data_smoke_test.py",
    ROOT / "scripts" / "mornye_syntony_field_healing_manifest_reapply_smoke_test.py",
    ROOT / "scripts" / "mornye_syntony_field_heal_scheduler_smoke_test.py",
    ROOT / "scripts" / "mornye_high_syntony_field_heal_scheduler_smoke_test.py",
    ROOT / "PROJECT_PROGRESS_STATE.json",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def assert_payload(record: dict, *, source_ref: str, multiplier: float) -> None:
    assert record["policy_selectable"] is False
    assert record["scheduled_event_type"] == "healing"
    assert record["hits"] == []
    assert record["damage_multiplier"] == 0.0
    assert record["off_tune_value"] == 0.0
    assert record["resonance_energy_gain"] == 0.0
    assert record["concerto_energy_gain"] == 0.0
    effects = record["mechanic_effects"]
    assert effects["source_status"] == "workbook_confirmed_scheduled_heal"
    assert effects["source_ref"] == source_ref
    assert effects["relative_tick_frames"] == NORMAL_FRAMES
    healing = effects["healing_metadata"]
    assert healing["base_heal"] == 1805.0
    assert healing["scaling_stat"] == "def"
    assert healing["scaling_multiplier"] == 0.945
    assert healing["field_healing_multiplier"] == multiplier


def main() -> None:
    assert [ord(c) for c in ROLE_FEMALE_SHEET] == [0x89D2, 0x8272, 0x002D, 0x5973]
    assert [ord(c) for c in SKILL_TYPE_SHEET] == [0x89D2, 0x8272, 0x6280, 0x80FD, 0x7C7B, 0x578B]

    texts = []
    for path in RELEVANT_FILES:
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"{path} has BOM"
        text = raw.decode("utf-8")
        texts.append(text)
    merged = "\n".join(texts)
    for bad in BAD_HEALING_SOURCE_MARKERS:
        assert bad not in merged, f"corrupted healing source reference remains: {bad!r}"

    actions = {row["id"]: row for row in load_json(DATA_DIR / "actions.json")}
    transitions = {row["id"]: row for row in load_json(DATA_DIR / "transition_actions.json")}
    assert actions["mornye_heavy_geopotential_shift"]["mechanic_effects"]["scheduled_healing_source_ref"] == NORMAL_HEAL_COMBINED_REF
    assert actions["mornye_liberation_critical_protocol"]["mechanic_effects"]["scheduled_healing_source_ref"] == HIGH_HEAL_COMBINED_REF
    assert transitions["mornye_intro_convergence"]["mechanic_effects"]["scheduled_healing_source_ref"] == NORMAL_HEAL_COMBINED_REF
    assert_payload(actions["mornye_syntony_field_heal"], source_ref=NORMAL_HEAL_COMBINED_REF, multiplier=1.0)
    assert_payload(actions["mornye_high_syntony_field_heal"], source_ref=HIGH_HEAL_COMBINED_REF, multiplier=1.4)

    root_manifest = (ROOT / "direct_action_data_patch_manifest_v61.json").read_bytes()
    source_manifest = (ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json").read_bytes()
    assert root_manifest == source_manifest
    manifest = json.loads(root_manifest.decode("utf-8"))
    section = manifest["mornye_syntony_field_healing_patches"]
    assert section["source_rows"]["normal_field"] == [NORMAL_FIELD_REF]
    assert section["source_rows"]["high_field"] == [HIGH_FIELD_REF]
    assert section["source_rows"]["normal_healing"] == [NORMAL_HEAL_ACTION_REF, HEAL_SKILL_REF]
    assert section["source_rows"]["high_healing"] == [HIGH_HEAL_ACTION_REF, HEAL_SKILL_REF]

    report = (ROOT / "reports" / "mornye_syntony_field_healing_scheduler_audit.md").read_text(encoding="utf-8")
    for expected in (
        NORMAL_FIELD_REF,
        HIGH_FIELD_REF,
        NORMAL_HEAL_ACTION_REF,
        HIGH_HEAL_ACTION_REF,
        HEAL_SKILL_REF,
        NORMAL_HEAL_COMBINED_REF,
        HIGH_HEAL_COMBINED_REF,
        "incoming transition actor",
    ):
        assert expected in report

    print("mornye_syntony_field_healing_source_traceability_smoke_test ok")


if __name__ == "__main__":
    main()
