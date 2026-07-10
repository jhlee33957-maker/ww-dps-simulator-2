from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation
from simulator.transition_actions import transition_action_to_action_data
from simulator.transition_config import load_transition_config


TRIGGER_ID = "aemeath_resonance_mode_damage_trigger"
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
NON_TRIGGER_ACTION_IDS = {
    "aemeath_basic_form_stage_1",
    "aemeath_basic_form_stage_2",
    "aemeath_mech_basic_stage_1",
    "aemeath_mech_basic_stage_2",
    "aemeath_seraphic_duet_overturn",
    "aemeath_seraphic_duet_encore",
    "aemeath_liberation_overdrive",
    "aemeath_heavenfall_finale",
    "aemeath_heavy_aemeath_charged_1",
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_1",
    "aemeath_heavy_mech_charged_2",
    "aemeath_form_switch_to_mech_normal",
    "aemeath_form_switch_to_aemeath_normal",
    "aemeath_form_switch_to_aemeath_after_overdrive",
}


def load_actions() -> dict[str, dict]:
    return {
        row["id"]: row
        for row in json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))
    }


def load_transition_records() -> dict[str, dict]:
    return {
        row["id"]: row
        for row in json.loads((DATA_DIR / "transition_actions.json").read_text(encoding="utf-8-sig"))
    }


def config_for_mode(mode: str) -> dict:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = mode
    return config


def make_sim(mode: str) -> Simulation:
    return Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        transition_config=config_for_mode(mode),
    )


def assert_trigger_shape(trigger: dict) -> None:
    assert trigger["trigger_id"] == TRIGGER_ID
    assert trigger["trigger_on"] == "damage_dealt"
    assert math.isclose(float(trigger["cooldown_seconds"]), 3.0)
    assert trigger["event_by_aemeath_resonance_mode"]["fusion_burst"] == "fusion_burst"
    assert trigger["event_by_aemeath_resonance_mode"]["tune_rupture"] == "tune_rupture_shifting"
    assert trigger["source_status"] == "user_supplied_skill_screenshot_not_embedded"


def test_trigger_metadata_is_on_expected_actions_only() -> None:
    actions = load_actions()
    for action_id in TRIGGER_ACTION_IDS:
        triggers = actions[action_id].get("mechanic_event_triggers") or []
        assert len(triggers) == 1, action_id
        assert_trigger_shape(triggers[0])

    for action_id in NON_TRIGGER_ACTION_IDS:
        assert not actions[action_id].get("mechanic_event_triggers"), action_id


def test_transition_action_converter_preserves_event_triggers() -> None:
    records = load_transition_records()
    for action_id in TRANSITION_TRIGGER_ACTION_IDS:
        record = records[action_id]
        triggers = record.get("mechanic_event_triggers") or []
        assert len(triggers) == 1, action_id
        assert_trigger_shape(triggers[0])
        action = transition_action_to_action_data(record)
        assert action.id == f"transition:{action_id}"
        assert action.policy_selectable is False
        assert len(action.mechanic_event_triggers) == 1
        assert_trigger_shape(action.mechanic_event_triggers[0])


def execute_trigger_action(mode: str, action_id: str = "aemeath_basic_form_stage_3") -> Simulation:
    sim = make_sim(mode)
    assert sim.execute_action(action_id), action_id
    return sim


def test_mode_event_emission_and_summary_counts() -> None:
    fusion_sim = execute_trigger_action("fusion_burst")
    fusion_row = fusion_sim.summary().timeline[-1]
    assert fusion_row.emitted_mechanic_event_tags == ["fusion_burst"]
    assert fusion_row.mechanic_event_triggered is True
    assert fusion_row.mechanic_event_cooldown_blocked is False
    assert fusion_row.aemeath_resonance_mode == "fusion_burst"
    assert fusion_sim.summary().fusion_burst_event_count == 1

    tune_sim = execute_trigger_action("tune_rupture")
    tune_summary = tune_sim.summary()
    tune_row = tune_summary.timeline[-1]
    assert tune_row.emitted_mechanic_event_tags == ["tune_rupture_shifting"]
    assert tune_summary.tune_rupture_shifting_event_count == 1

    unresolved_sim = execute_trigger_action("unresolved")
    unresolved_summary = unresolved_sim.summary()
    unresolved_row = unresolved_summary.timeline[-1]
    assert unresolved_row.emitted_mechanic_event_tags == []
    assert unresolved_row.mechanic_event_triggered is False
    assert unresolved_row.mechanic_event_unresolved_reason == "aemeath_resonance_mode_unresolved_no_events_emit"
    assert unresolved_summary.mechanic_event_unresolved_reason == "aemeath_resonance_mode_unresolved_no_events_emit"


def test_same_skill_cooldown_and_lumped_hit_single_event() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    first_row = sim.summary().timeline[-1]
    assert first_row.hit_count == 1
    assert first_row.emitted_mechanic_event_tags == ["fusion_burst"]
    assert sim.summary().fusion_burst_event_count == 1

    assert sim.execute_action("aemeath_basic_form_stage_3")
    second_row = sim.summary().timeline[-1]
    assert second_row.emitted_mechanic_event_tags == []
    assert second_row.mechanic_event_cooldown_blocked is True
    assert sim.summary().fusion_burst_event_count == 1

    sim.state.combat_time += 3.0
    sim.state.current_time += 3.0
    assert sim.execute_action("aemeath_basic_form_stage_3")
    third_row = sim.summary().timeline[-1]
    assert third_row.emitted_mechanic_event_tags == ["fusion_burst"]
    assert sim.summary().fusion_burst_event_count == 2


def test_event_mode_adds_no_damage() -> None:
    unresolved_damage = execute_trigger_action("unresolved").summary().timeline[-1].total_action_damage
    fusion_damage = execute_trigger_action("fusion_burst").summary().timeline[-1].total_action_damage
    tune_damage = execute_trigger_action("tune_rupture").summary().timeline[-1].total_action_damage
    assert math.isclose(fusion_damage, unresolved_damage, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(tune_damage, unresolved_damage, rel_tol=1e-9, abs_tol=1e-9)


def test_user_real_aemeath_profile_still_present() -> None:
    profiles = json.loads((DATA_DIR / "build_profiles.json").read_text(encoding="utf-8-sig"))
    profile = profiles["profiles"]["aemeath"]["aemeath_user_real_01"]
    atk = profile["stat_components"]["atk"]
    assert atk == {
        "character_base": 424,
        "weapon_base": 587.5,
        "percent": 1.133,
        "flat": 500,
        "final_reference": 2657,
    }
    assert isinstance(profile["damage_bonuses"]["by_element"]["generic"], (int, float))
    assert isinstance(profile["damage_bonuses"]["by_element"]["fusion"], (int, float))
    assert profile["damage_bonuses"]["by_category"]["resonance_skill"] == 0.101
    assert profile["damage_bonuses"]["by_category"]["resonance_liberation"] == 0.688


def main() -> None:
    test_trigger_metadata_is_on_expected_actions_only()
    test_transition_action_converter_preserves_event_triggers()
    test_mode_event_emission_and_summary_counts()
    test_same_skill_cooldown_and_lumped_hit_single_event()
    test_event_mode_adds_no_damage()
    test_user_real_aemeath_profile_still_present()
    print("aemeath_resonance_mode_mechanic_event_smoke_test ok")


if __name__ == "__main__":
    main()
