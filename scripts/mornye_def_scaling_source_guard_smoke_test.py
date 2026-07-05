from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.build_profiles import build_action_scaling_summary
from simulator.models import ActionData
from simulator.simulation import Simulation
from simulator.transition_actions import get_transition_action, transition_action_to_action_data


EXPECTED_DEF_ACTIONS = {
    "mornye_basic_stage_1",
    "mornye_basic_stage_2",
    "mornye_basic_stage_3",
    "mornye_basic_stage_4",
    "mornye_wfo_basic_stage_1",
    "mornye_wfo_basic_stage_2",
    "mornye_wfo_basic_stage_3",
    "mornye_heavy_attack_normal",
    "mornye_heavy_geopotential_shift",
    "mornye_heavy_inversion",
    "mornye_skill_optimal_solution",
    "mornye_skill_distributed_array",
    "mornye_liberation_critical_protocol",
    "mornye_syntony_field_damage",
    "mornye_intro_convergence",
}


def load_actions() -> dict[str, dict]:
    return {item["id"]: item for item in json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))}


def test_mornye_damage_actions_are_def_scaling() -> None:
    actions = load_actions()
    for action_id in EXPECTED_DEF_ACTIONS:
        action = actions[action_id]
        assert action["scaling_stat"] == "def", action_id
        assert action["scaling_stat_source"] == "user_supplied_skill_screenshot"
        assert action["scaling_stat_source_status"] == "user_supplied_screenshot_not_embedded"
    assert actions["mornye_skill_expectation_error"]["scaling_stat"] == "none"


def test_source_note_and_summary() -> None:
    note = json.loads((DATA_DIR / "extracted" / "mornye_scaling_stat_source_note.json").read_text(encoding="utf-8"))
    assert note["character_id"] == "mornye"
    assert note["scaling_stat"] == "def"
    assert note["source_status"] == "user_supplied_screenshot_not_embedded"
    assert set(note["affected_action_ids"]) == EXPECTED_DEF_ACTIONS
    action_models = [ActionData.model_validate(item) for item in load_actions().values()]
    summary = build_action_scaling_summary(action_models, ["mornye"])["mornye"]
    assert not summary["unresolved_scaling_actions"]
    assert set(summary["actions_requiring_def_stats"]) >= EXPECTED_DEF_ACTIONS
    assert not any(action_id in summary["actions_requiring_atk_stats"] for action_id in EXPECTED_DEF_ACTIONS)


def test_mornye_real_manual_requires_def() -> None:
    sim = Simulation.from_json(DATA_DIR, party="mornye", build_profile_overrides={"mornye": "mornye_real_manual"})
    validation = sim.validate_build_profiles()
    assert validation["ok"] is False
    message = "\n".join(validation["errors"])
    assert "mornye:mornye_real_manual" in message
    assert "stat_components.def.character_base" in message
    assert "stat_components.def.final_reference" in message


def test_mornye_intro_transition_is_def_scaling() -> None:
    record = get_transition_action(DATA_DIR, "mornye_intro_convergence")
    assert record is not None
    assert record["scaling_stat"] == "def"
    assert record["scaling_stat_source"] == "user_supplied_skill_screenshot"
    assert record["scaling_stat_source_status"] == "user_supplied_screenshot_not_embedded"
    assert "DEF-scaling" in record["scaling_stat_note"]

    action = transition_action_to_action_data(record)
    assert action.id == "transition:mornye_intro_convergence"
    assert action.action_type == "swap"
    assert action.policy_selectable is False
    assert action.scaling_stat == "def"
    assert action.scaling_stat_source == "user_supplied_skill_screenshot"
    assert action.scaling_stat_source_status == "user_supplied_screenshot_not_embedded"
    assert action.scaling_stat_note == record["scaling_stat_note"]


def main() -> None:
    test_mornye_damage_actions_are_def_scaling()
    test_source_note_and_summary()
    test_mornye_real_manual_requires_def()
    test_mornye_intro_transition_is_def_scaling()
    print("mornye_def_scaling_source_guard_smoke_test ok")


if __name__ == "__main__":
    main()
