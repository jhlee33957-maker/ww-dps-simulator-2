from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


AUDIT_JSON = DATA_DIR / "extracted" / "aemeath_resonance_mode_mechanic_source_audit.json"
AUDIT_MD = PROJECT_ROOT / "reports" / "aemeath_resonance_mode_mechanic_source_audit.md"
TRIGGER_ACTION_IDS = {
    "aemeath_basic_form_stage_3",
    "aemeath_basic_form_stage_4",
    "aemeath_mech_basic_stage_3",
    "aemeath_mech_basic_stage_4",
    "aemeath_sync_strike_armament_merge",
    "aemeath_sync_strike_call_of_dawn",
}
TRANSITION_TRIGGER_ACTION_IDS = {
    "aemeath_qte_intro_human",
    "aemeath_qte_intro_mech",
}


def main() -> None:
    assert AUDIT_JSON.exists(), AUDIT_JSON
    assert AUDIT_MD.exists(), AUDIT_MD
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8-sig"))
    report_text = AUDIT_MD.read_text(encoding="utf-8")

    assert audit["character_id"] == "aemeath"
    assert audit["source_status"] == "user_supplied_skill_screenshot_not_embedded"
    assert audit["implemented_status"] == "event_trigger_only"
    assert audit["workbook_confirmation"]["status"] == "not_clearly_confirmed"
    assert set(audit["trigger_action_ids"]) == TRIGGER_ACTION_IDS
    assert set(audit["transition_trigger_action_ids"]) == TRANSITION_TRIGGER_ACTION_IDS
    assert audit["unmapped_expected_trigger_skills"] == []
    assert audit["trigger_rule"]["same_skill_cooldown_seconds"] == 3.0
    assert audit["trigger_rule"]["event_by_aemeath_resonance_mode"]["fusion_burst"] == "fusion_burst"
    assert (
        audit["trigger_rule"]["event_by_aemeath_resonance_mode"]["tune_rupture"]
        == "tune_rupture_shifting"
    )
    assert audit["trigger_rule"]["event_by_aemeath_resonance_mode"]["unresolved"] is None
    assert audit["damage_added_by_this_patch"] == 0.0
    assert audit["reward_formula_changed"] is False

    for expected in (
        "user_supplied_skill_screenshot_not_embedded",
        "event_trigger_only",
        "not clearly embed",
        "does not add Fusion Burst damage",
        "aemeath_basic_form_stage_3",
        "aemeath_qte_intro_human",
    ):
        assert expected in report_text, expected

    print("aemeath_resonance_mode_source_audit_smoke_test ok")


if __name__ == "__main__":
    main()
