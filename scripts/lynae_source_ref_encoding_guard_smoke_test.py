from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.source_ref_canonicalization import (
    CANONICAL_BOSS_COOLDOWN_SHEET,
    CANONICAL_BOSS_COOLDOWN_SOURCE_REF,
    CANONICAL_LYNAE_ACTION_SHEET,
    CANONICAL_LYNAE_SKILL_TYPE_SHEET,
    bad_markers,
)

SPRAY_PAINT_REFS = [f"{CANONICAL_LYNAE_ACTION_SHEET}!{row}" for row in range(2683, 2689)]
SPRAY_PAINT_PATHS = [
    ROOT / "data" / "actions.json",
    ROOT / "characters" / "lynae.py",
    ROOT / "simulator" / "simulation.py",
    ROOT / "direct_action_data_patch_manifest_v61.json",
    ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json",
    ROOT / "reports" / "lynae_spray_paint_scheduler_audit.md",
]


def spray_paint_extra_bad_markers() -> list[str]:
    return [
        chr(0x6B32) + chr(0xB000),
        chr(0x6B32) + chr(0xB000) + chr(0x3F) + chr(0x3F) + chr(0x3F) + chr(0x963F) + chr(0x3F),
        chr(0x963F) + chr(0x3F),
        chr(0xFFFD),
    ]


def scan_paths() -> list[Path]:
    paths: set[Path] = set()
    paths.update((ROOT / "data").glob("*.json"))
    paths.update((ROOT / "data" / "mechanics").glob("*.json"))
    paths.update((ROOT / "data" / "extracted").glob("*.json"))
    paths.update((ROOT / "scripts").glob("*.py"))
    paths.update((ROOT / "reports").glob("*.md"))
    return sorted(path for path in paths if path.is_file() and path.suffix in {".json", ".py", ".md"})


def assert_no_corrupt_markers() -> None:
    for path in scan_paths():
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise AssertionError(f"UTF-8 BOM found in {path}")
        text = raw.decode("utf-8")
        for marker in [*bad_markers(), *spray_paint_extra_bad_markers()]:
            if marker in text:
                raise AssertionError(f"corrupt source encoding marker {marker!r} found in {path}")


def assert_tune_break_source_refs() -> None:
    party_presets = json.loads((ROOT / "data" / "party_presets.json").read_text(encoding="utf-8"))
    for preset in party_presets:
        tune_break_system = (preset.get("mechanic_overrides") or {}).get("tune_break_system")
        if tune_break_system and "enemy_tune_break_cooldown_source_ref" in tune_break_system:
            assert tune_break_system["enemy_tune_break_cooldown_source_ref"] == CANONICAL_BOSS_COOLDOWN_SOURCE_REF, preset["party_id"]

    transition_config = json.loads((ROOT / "data" / "transition_config.json").read_text(encoding="utf-8"))
    default_tune_break = transition_config["mechanics"]["tune_break_system"]
    assert default_tune_break["enemy_tune_break_cooldown_source_ref"] == CANONICAL_BOSS_COOLDOWN_SOURCE_REF
    assert CANONICAL_BOSS_COOLDOWN_SHEET in default_tune_break["enemy_tune_break_cooldown_source_ref"]


def assert_lynae_generator_and_outputs() -> None:
    source_audit = (ROOT / "scripts" / "lynae_source_audit.py").read_text(encoding="utf-8")
    assert CANONICAL_LYNAE_ACTION_SHEET in source_audit
    assert CANONICAL_LYNAE_SKILL_TYPE_SHEET in source_audit

    timing_json = json.loads((ROOT / "data" / "extracted" / "lynae_timing_cooldown_audit.json").read_text(encoding="utf-8"))
    assert timing_json["source_region"] == f"{CANONICAL_LYNAE_ACTION_SHEET}2577:2738"
    assert timing_json["skill_type_region"] == f"{CANONICAL_LYNAE_SKILL_TYPE_SHEET}2612:2617"

    timing_report = (ROOT / "reports" / "lynae_timing_cooldown_audit.md").read_text(encoding="utf-8")
    alignment_report = (ROOT / "reports" / "lynae_excel_source_alignment.md").read_text(encoding="utf-8")
    assert f"{CANONICAL_LYNAE_ACTION_SHEET}2577:2738" in timing_report
    assert f"{CANONICAL_LYNAE_SKILL_TYPE_SHEET}2612:2617" in timing_report
    assert f"{CANONICAL_LYNAE_ACTION_SHEET}2703" in alignment_report
    assert f"{CANONICAL_LYNAE_ACTION_SHEET}2704" in alignment_report


def assert_spray_paint_source_refs() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in SPRAY_PAINT_PATHS)
    for ref in SPRAY_PAINT_REFS:
        assert ref in combined, ref

    actions = json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))
    by_id = {record["id"]: record for record in actions}
    schedule = by_id["lynae_visual_impact"]["mechanic_effects"]["spray_paint_status_schedule"]
    assert schedule["mode_mapping"]["tune_strain"]["source_row"] == SPRAY_PAINT_REFS[0]
    assert schedule["mode_mapping"]["tune_rupture"]["source_row"] == SPRAY_PAINT_REFS[1]
    assert schedule["c1_rows_excluded"] == SPRAY_PAINT_REFS[2:]


def main() -> None:
    assert_no_corrupt_markers()
    assert_tune_break_source_refs()
    assert_lynae_generator_and_outputs()
    assert_spray_paint_source_refs()
    print("lynae_source_ref_encoding_guard_smoke_test ok")


if __name__ == "__main__":
    main()
