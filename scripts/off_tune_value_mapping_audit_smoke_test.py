from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


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
    assert_close(action_by_id("mornye_syntony_field_damage")["off_tune_value"], 66.4, "Syntony Field")
    assert_close(action_by_id("aemeath_mech_basic_stage_1")["off_tune_value"], 13.34, "Aemeath mech stage 1")
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

    report = report_path.read_text(encoding="utf-8")
    assert "mornye_heavy_inversion" in report
    assert "角色-女!S4136" in report

    print("off_tune_value_mapping_audit_smoke_test ok")


if __name__ == "__main__":
    main()
