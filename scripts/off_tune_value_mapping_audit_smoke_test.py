from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation

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


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def action_by_id(action_id: str) -> dict:
    actions = read_json(ROOT / "data" / "actions.json")
    return {action["id"]: action for action in actions}[action_id]


def transition_by_id(action_id: str) -> dict:
    actions = read_json(ROOT / "data" / "transition_actions.json")
    return {action["id"]: action for action in actions}[action_id]


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-6) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def main() -> None:
    target_actions = {
        "aemeath_form_switch_to_mech_normal",
        "aemeath_form_switch_to_aemeath_normal",
        "aemeath_form_switch_to_aemeath_after_overdrive",
        "aemeath_seraphic_duet_encore",
    }
    audit_path = ROOT / "data" / "extracted" / "off_tune_value_mapping_audit.json"
    report_path = ROOT / "reports" / "off_tune_value_mapping_audit.md"
    assert audit_path.exists()
    assert report_path.exists()

    audit = read_json(audit_path)
    notes = audit.get("notes", [])
    assert notes.count(DAMAGE_1_NOTE) == 1
    assert notes.count(DAMAGE_2_NOTE) == 1
    for legacy_note in LEGACY_NOTE_VARIANTS:
        assert legacy_note not in notes
    assert audit["boss_tune_break_cooldown_seconds"] == 3.0
    assert audit["boss_tune_break_cooldown_source_ref"] == "附页2!B227"
    assert audit["cooldown_blocks_off_tune_accumulation"] is True
    assert "damaging_actions_checked" in audit
    assert "unresolved_damaging_action_ids" in audit
    assert "internal_alias_action_ids" in audit
    assert target_actions.issubset(set(audit["damaging_actions_checked"]))
    assert target_actions.issubset(set(audit["actions_with_missing_off_tune_metadata_before_patch"]))
    assert "aemeath_seraphic_duet_encore" in {row["action_id"] for row in audit["actions_fixed_this_patch"]}
    assert audit["unresolved_damaging_action_ids"] == []
    assert set(audit["internal_alias_action_ids"]) == {
        "aemeath_form_switch_to_mech_normal",
        "aemeath_form_switch_to_aemeath_normal",
        "aemeath_form_switch_to_aemeath_after_overdrive",
    }

    assert_close(action_by_id("mornye_heavy_geopotential_shift")["off_tune_value"], 29.6, "Geopotential Shift")
    assert action_by_id("mornye_heavy_geopotential_shift")["off_tune_value_source_ref"] == "角色-女!S4117"
    assert_close(action_by_id("mornye_heavy_inversion")["off_tune_value"], 104.0, "Inversion")
    assert action_by_id("mornye_heavy_inversion")["off_tune_value_source_ref"] == "角色-女!S4136"
    assert_close(action_by_id("mornye_wfo_basic_stage_1")["off_tune_value"], 7.0, "WFO stage 1")
    damage_1_action = action_by_id("mornye_syntony_field_damage")
    assert_close(damage_1_action["off_tune_value"], 0.0, "Syntony Field Damage 1")
    assert damage_1_action["off_tune_value_source_status"] == "workbook_confirmed_zero_for_damage_1"
    assert DAMAGE_1_ACTION_REF in damage_1_action["off_tune_value_source_ref"]
    damage_2_action = action_by_id("mornye_syntony_field_target_damage")
    assert_close(damage_2_action["off_tune_value"], 66.4, "Syntony Field Damage 2")
    assert damage_2_action["off_tune_value_source_status"] == "workbook_confirmed"
    assert DAMAGE_2_ACTION_REF in damage_2_action["off_tune_value_source_ref"]
    assert_close(action_by_id("aemeath_mech_basic_stage_1")["off_tune_value"], 13.34, "Aemeath mech stage 1")
    mech_a3 = action_by_id("aemeath_mech_basic_stage_3")
    assert_close(mech_a3["off_tune_value"], 62.54, "Aemeath mech stage 3 repeat-aware")
    assert mech_a3["off_tune_value_source_status"] == "workbook_confirmed_repeat_aware"
    assert mech_a3["off_tune_value_repeat_formula"] == "6.7 + 2.24 * 3 + 2.24 + 46.88"
    assert_close(action_by_id("aemeath_sync_strike_call_of_dawn")["off_tune_value"], 93.86, "Call of Dawn")
    assert_close(action_by_id("aemeath_heavy_mech_charged_2")["off_tune_value"], 133.36, "Mech charged 2")
    assert_close(transition_by_id("aemeath_qte_intro_human")["off_tune_value"], 77.37, "Aemeath human QTE")
    assert_close(transition_by_id("aemeath_qte_intro_mech")["off_tune_value"], 93.85, "Aemeath mech QTE")
    assert_close(transition_by_id("mornye_intro_convergence")["off_tune_value"], 136.0, "Mornye intro")
    assert_close(action_by_id("aemeath_form_switch_to_mech_normal")["off_tune_value"], 13.34, "Form switch to mech")
    assert action_by_id("aemeath_form_switch_to_mech_normal")["off_tune_value_alias_of"] == "aemeath_mech_basic_stage_1"
    assert_close(
        action_by_id("aemeath_form_switch_to_aemeath_normal")["off_tune_value"],
        26.64,
        "Form switch to Aemeath",
    )
    assert_close(
        action_by_id("aemeath_form_switch_to_aemeath_after_overdrive")["off_tune_value"],
        39.93,
        "Post-Overdrive form switch",
    )
    assert_close(action_by_id("aemeath_seraphic_duet_encore")["off_tune_value"], 128.0, "Seraphic Duet Encore")
    assert action_by_id("aemeath_seraphic_duet_encore")["off_tune_value_source_ref"] == "角色-女!S2925:S2929"

    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    summary = sim.summary()
    assert summary.enemy_tune_break_cooldown_seconds == 3.0
    assert summary.enemy_tune_break_cooldown_source_ref == "附页2!B227"
    assert summary.mapped_off_tune_action_count >= 25
    assert summary.unresolved_off_tune_damaging_action_ids == []
    assert summary.off_tune_mapping_completeness_status == "complete"
    assert summary.off_tune_value_mapping_source_report == "reports/off_tune_value_mapping_audit.md"

    three_party_sim = Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
    )
    three_party_summary = three_party_sim.summary()
    assert three_party_summary.mapped_off_tune_action_count >= summary.mapped_off_tune_action_count
    assert three_party_summary.unresolved_off_tune_damaging_action_ids == ["lynae_echo_hyvatia"]
    assert three_party_summary.off_tune_mapping_completeness_status == "incomplete"
    assert "reports/lynae_off_tune_direct_mapping_audit.md" in (
        three_party_summary.off_tune_value_mapping_source_report
    )

    report = report_path.read_text(encoding="utf-8")
    mapping = {row["action_id"]: row for row in audit["mappings"]}["aemeath_mech_basic_stage_3"]
    assert_close(mapping["off_tune_value"], 62.54, "Aemeath mech stage 3 mapping")
    assert mapping["source_status"] == "workbook_confirmed_repeat_aware"
    assert mapping["repeat_formula"] == "6.7 + 2.24 * 3 + 2.24 + 46.88"
    mappings_by_id = {row["action_id"]: row for row in audit["mappings"]}
    damage_1_mapping = mappings_by_id["mornye_syntony_field_damage"]
    assert_close(damage_1_mapping["off_tune_value"], 0.0, "Damage 1 audit mapping")
    assert damage_1_mapping["source_status"] == "workbook_confirmed_zero_for_damage_1"
    assert DAMAGE_1_ACTION_REF in damage_1_mapping["source_ref"]
    assert damage_1_mapping["policy_selectable"] is False
    assert damage_1_mapping["damaging_action"] is True
    assert damage_1_mapping["note"] == DAMAGE_1_NOTE

    damage_2_mapping = mappings_by_id["mornye_syntony_field_target_damage"]
    assert_close(damage_2_mapping["off_tune_value"], 66.4, "Damage 2 audit mapping")
    assert damage_2_mapping["source_status"] == "workbook_confirmed"
    assert DAMAGE_2_ACTION_REF in damage_2_mapping["source_ref"]
    assert damage_2_mapping["policy_selectable"] is False
    assert damage_2_mapping["damaging_action"] is True
    assert damage_2_mapping["note"] == DAMAGE_2_NOTE
    assert "mornye_syntony_field_damage" in audit["damaging_actions_checked"]
    assert "mornye_syntony_field_target_damage" in audit["damaging_actions_checked"]
    assert report.count("`mornye_syntony_field_damage`") == 1
    assert report.count("`mornye_syntony_field_target_damage`") == 1
    assert report.count(DAMAGE_1_NOTE) == 1
    assert report.count(DAMAGE_2_NOTE) == 1
    for legacy_note in LEGACY_NOTE_VARIANTS:
        assert legacy_note not in report
    assert "mornye_heavy_inversion" in report
    assert "角色-女!S4136" in report

    print("off_tune_value_mapping_audit_smoke_test ok")


if __name__ == "__main__":
    main()
