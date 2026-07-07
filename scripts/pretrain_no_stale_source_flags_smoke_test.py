from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AEMEATH_FORTE_PATH = PROJECT_ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json"
ACTIONS_PATH = PROJECT_ROOT / "data" / "actions.json"
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "pretrain_aemeath_mornye_source_lock_audit.py"
AUDIT_JSON = PROJECT_ROOT / "data" / "extracted" / "pretrain_aemeath_mornye_source_lock_audit.json"

NORMAL_LABEL = "\u5f3a\u5316E-\u9707\u8c10"
ENHANCED_LABEL = "\u5f3a\u5316E-\u9707\u8c10\u589e\u5e45"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def assert_not_stale_source_status(value: str | None, label: str) -> None:
    stale_statuses = {
        "unresolved_no_runtime_effect",
        "scaffold_only_until_source_confirmed",
        "manual_placeholder",
    }
    assert value not in stale_statuses, f"{label} still has stale source status {value!r}"


def test_aemeath_forte_followups() -> None:
    config = load_json(AEMEATH_FORTE_PATH)
    followups = {
        entry["variant"]: entry
        for entry in config["modes"]["tune_rupture"]["seraphic_duet_followups"]
    }
    normal = followups["normal"]
    enhanced = followups["enhanced"]

    assert normal["label"] == NORMAL_LABEL
    assert normal["formula_type"] == "tune_response"
    assert normal["tune_multiplier"] == 1.0935
    assert normal["repeat_count"] == 5
    assert normal["source_status"] == "workbook_confirmed"
    assert_not_stale_source_status(normal.get("source_status"), "normal Seraphic Duet follow-up")

    assert enhanced["label"] == ENHANCED_LABEL
    assert enhanced["formula_type"] == "tune_response"
    assert enhanced["tune_multiplier"] == 1.0935
    assert enhanced["repeat_count"] == 10
    assert enhanced["source_status"] == "workbook_confirmed"
    assert_not_stale_source_status(enhanced.get("source_status"), "enhanced Seraphic Duet follow-up")

    fusion_burst = config["modes"]["fusion_burst"]
    assert fusion_burst["implementation_status"] == "scaffold_only_until_source_confirmed"
    unresolved_entries = json.dumps(fusion_burst["unresolved_entries"], ensure_ascii=False).lower()
    assert "fusion burst" in unresolved_entries
    assert "unresolved_no_runtime_effect" in unresolved_entries


def test_aemeath_unsupported_followups() -> None:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from simulator.mechanic_events import UNSUPPORTED_AEMEATH_FOLLOWUP_MECHANICS

    unsupported_text = json.dumps(UNSUPPORTED_AEMEATH_FOLLOWUP_MECHANICS, ensure_ascii=False).lower()
    forbidden_terms = (
        "tune_rupture_followup",
        "seraphic_duet_tune_rupture",
        NORMAL_LABEL.lower(),
        ENHANCED_LABEL.lower(),
    )
    for term in forbidden_terms:
        assert term not in unsupported_text, f"implemented follow-up still listed unsupported: {term}"
    assert "fusion_burst" in unsupported_text or "fusion burst" in unsupported_text


def test_mornye_repeat_aware_source_flags() -> None:
    actions = {action["id"]: action for action in load_json(ACTIONS_PATH)}
    expected = {
        "mornye_wfo_basic_stage_1": (10.0, [4128], "2.5 x 4"),
        "mornye_wfo_basic_stage_2": (12.0, [4129], "3 x 4"),
    }
    for action_id, (momentum_delta, rows, calculation) in expected.items():
        effects = actions[action_id]["mechanic_effects"]
        assert effects["relative_momentum_delta"] == momentum_delta
        assert effects["relative_momentum_gain_source_rows"] == rows
        assert effects["source_rows"] == rows
        assert effects["source_status"] == "workbook_confirmed_repeat_aware"
        assert effects["relative_momentum_repeat_calculation"] == calculation
        assert_not_stale_source_status(effects.get("source_status"), action_id)


def test_audit_has_no_source_confirmed_mismatches() -> None:
    if not AUDIT_JSON.exists():
        subprocess.run([sys.executable, str(AUDIT_SCRIPT)], cwd=PROJECT_ROOT, check=True)
    audit = load_json(AUDIT_JSON)
    assert audit["source_confirmed_mismatches"] == []
    sections = {section["id"]: section for section in audit["sections"]}
    implemented_section_ids = {
        "aemeath_forte_followup",
        "aemeath_overdrive_forte_state",
        "aemeath_mech_basic_stage_3_repeat_aware",
        "aemeath_tune_break_starburst",
        "mornye_relative_momentum",
        "mornye_interfered_marker",
        "mornye_tune_break_particle_jet",
    }
    for section_id in implemented_section_ids:
        section = sections[section_id]
        assert section["status"] == "PASS", section
        assert not section["mismatches"], section


def main() -> None:
    test_aemeath_forte_followups()
    test_aemeath_unsupported_followups()
    test_mornye_repeat_aware_source_flags()
    test_audit_has_no_source_confirmed_mismatches()
    print("pretrain_no_stale_source_flags_smoke_test ok")


if __name__ == "__main__":
    main()
