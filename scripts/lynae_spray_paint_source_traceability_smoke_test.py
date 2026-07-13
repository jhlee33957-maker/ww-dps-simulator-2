from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.source_ref_canonicalization import bad_markers
from lynae_spray_paint_test_helpers import (
    C1_OUT_OF_SCOPE_REFS,
    ROLE_FEMALE_SHEET,
    TUNE_RUPTURE_REF,
    TUNE_STRAIN_REF,
    assert_canonical_source_refs,
)


RELEVANT_FILES = [
    ROOT / "data" / "actions.json",
    ROOT / "characters" / "lynae.py",
    ROOT / "simulator" / "simulation.py",
    ROOT / "direct_action_data_patch_manifest_v61.json",
    ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json",
    ROOT / "reports" / "lynae_spray_paint_scheduler_audit.md",
    ROOT / "scripts" / "lynae_spray_paint_payload_data_smoke_test.py",
    ROOT / "scripts" / "lynae_spray_paint_mode_snapshot_smoke_test.py",
    ROOT / "scripts" / "lynae_spray_paint_scheduler_smoke_test.py",
    ROOT / "scripts" / "lynae_spray_paint_recast_smoke_test.py",
    ROOT / "scripts" / "scheduled_status_application_smoke_test.py",
    ROOT / "scripts" / "combat_time_effect_duration_smoke_test.py",
    ROOT / "PROJECT_PROGRESS_STATE.json",
]


def spray_paint_extra_bad_markers() -> list[str]:
    return [
        chr(0x6B32) + chr(0xB000),
        chr(0x6B32) + chr(0xB000) + chr(0x3F) + chr(0x3F) + chr(0x3F) + chr(0x963F) + chr(0x3F),
        chr(0x963F) + chr(0x3F),
        chr(0xFFFD),
    ]


def read_text_no_bom(path: Path) -> str:
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{path} has UTF-8 BOM"
    return raw.decode("utf-8")


def assert_no_corruption(text: str, path: Path) -> None:
    forbidden = [*bad_markers(), *spray_paint_extra_bad_markers()]
    for marker in forbidden:
        assert marker not in text, f"corrupt marker {marker!r} found in {path}"


def main() -> None:
    assert_canonical_source_refs()
    assert ROLE_FEMALE_SHEET == "\u89d2\u8272-\u5973"

    texts = {path: read_text_no_bom(path) for path in RELEVANT_FILES}
    for path, text in texts.items():
        assert_no_corruption(text, path)

    combined = "\n".join(texts.values())
    for ref in [TUNE_STRAIN_REF, TUNE_RUPTURE_REF, *C1_OUT_OF_SCOPE_REFS]:
        assert ref in combined, f"missing canonical Spray Paint ref {ref}"

    actions = json.loads(texts[ROOT / "data" / "actions.json"])
    by_id = {record["id"]: record for record in actions}
    payload = by_id["lynae_spray_paint_flux_application"]
    assert payload["policy_selectable"] is False
    assert payload["scheduled_event_type"] == "status_application"
    assert payload["hits"] == []
    assert payload["damage_multiplier"] == 0.0
    assert payload["tune_break_multiplier"] == 0.0
    assert payload["off_tune_value"] == 0.0
    assert payload["resonance_energy_gain"] == 0.0
    assert payload["concerto_energy_gain"] == 0.0
    assert payload["cooldown"] == 0.0
    assert TUNE_STRAIN_REF in payload["off_tune_value_source_ref"]
    assert TUNE_RUPTURE_REF in payload["off_tune_value_source_ref"]

    schedule = by_id["lynae_visual_impact"]["mechanic_effects"]["spray_paint_status_schedule"]
    assert schedule["first_check_frames"] == 1
    assert schedule["check_interval_frames"] == 120
    assert schedule["field_duration_frames"] == 300
    assert schedule["relative_application_frames"] == [1, 121, 241]
    assert schedule["max_application_count"] == 3
    assert schedule["remove_on_max_trigger_count"] is False
    assert schedule["mode_mapping"]["tune_strain"]["source_row"] == TUNE_STRAIN_REF
    assert schedule["mode_mapping"]["tune_rupture"]["source_row"] == TUNE_RUPTURE_REF
    assert schedule["mode_mapping"]["tune_strain"]["target_shift_state"] == "tune_strain_shifting"
    assert schedule["mode_mapping"]["tune_rupture"]["target_shift_state"] == "tune_rupture_shifting"
    assert schedule["c1_rows_excluded"] == C1_OUT_OF_SCOPE_REFS

    report = texts[ROOT / "reports" / "lynae_spray_paint_scheduler_audit.md"]
    assert "out of scope" in report
    for ref in C1_OUT_OF_SCOPE_REFS:
        assert ref in report

    manifest_a = (ROOT / "direct_action_data_patch_manifest_v61.json").read_bytes()
    manifest_b = (ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json").read_bytes()
    assert manifest_a == manifest_b

    test_text = "\n".join(
        text for path, text in texts.items() if path.name.endswith("_smoke_test.py")
    )
    assert_no_corruption(test_text, ROOT / "scripts")
    print("lynae_spray_paint_source_traceability_smoke_test ok")


if __name__ == "__main__":
    main()
