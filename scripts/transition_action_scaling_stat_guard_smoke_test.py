from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.transition_actions import TransitionActionError, transition_action_to_action_data


DIRECT_DAMAGE_SCALING_STATS = {"atk", "def", "hp", "unresolved"}
MORNYE_SCALING_NOTE = (
    "Mornye damage is DEF-scaling per user-provided skill description; project should archive "
    "source screenshot or text before final validation."
)


def load_transition_records() -> dict[str, dict]:
    records = json.loads((DATA_DIR / "transition_actions.json").read_text(encoding="utf-8-sig"))
    return {record["id"]: record for record in records}


def has_direct_damage(record: dict) -> bool:
    return bool(record.get("hits"))


def test_direct_damage_transition_records_have_resolved_scaling() -> None:
    for record in load_transition_records().values():
        if not has_direct_damage(record):
            continue
        assert record.get("scaling_stat") in DIRECT_DAMAGE_SCALING_STATS, record["id"]
        assert record.get("scaling_stat") != "none", record["id"]


def test_expected_transition_scaling_stats_and_metadata() -> None:
    records = load_transition_records()
    assert records["aemeath_qte_intro_human"]["scaling_stat"] == "atk"
    assert records["aemeath_qte_intro_mech"]["scaling_stat"] == "atk"

    mornye = records["mornye_intro_convergence"]
    assert mornye["scaling_stat"] == "def"
    assert mornye["scaling_stat_source"] == "user_supplied_skill_screenshot"
    assert mornye["scaling_stat_source_status"] == "user_supplied_screenshot_not_embedded"
    assert mornye["scaling_stat_note"] == MORNYE_SCALING_NOTE


def test_converter_preserves_transition_scaling_and_source_metadata() -> None:
    records = load_transition_records()
    for action_id, expected_scaling in (
        ("aemeath_qte_intro_human", "atk"),
        ("aemeath_qte_intro_mech", "atk"),
        ("mornye_intro_convergence", "def"),
    ):
        action = transition_action_to_action_data(records[action_id])
        assert action.id == f"transition:{action_id}"
        assert action.action_type == "swap"
        assert action.policy_selectable is False
        assert action.scaling_stat == expected_scaling
        assert action.damage_bonus_category == records[action_id]["damage_bonus_category"]
        assert action.raw_skill_category == records[action_id]["metadata"]["raw_skill_category"]
        assert action.raw_damage_type == records[action_id]["metadata"]["raw_damage_type"]

    mornye = transition_action_to_action_data(records["mornye_intro_convergence"])
    assert mornye.damage_element == "fusion"
    assert mornye.scaling_stat_source == "user_supplied_skill_screenshot"
    assert mornye.scaling_stat_source_status == "user_supplied_screenshot_not_embedded"
    assert mornye.scaling_stat_note == MORNYE_SCALING_NOTE


def test_converter_rejects_direct_damage_with_none_scaling() -> None:
    record = dict(load_transition_records()["aemeath_qte_intro_human"])
    record["scaling_stat"] = "none"
    try:
        transition_action_to_action_data(record)
    except TransitionActionError as exc:
        assert "direct damage" in str(exc)
        assert "scaling_stat" in str(exc)
    else:
        raise AssertionError("direct-damage transition action with scaling_stat='none' was accepted")


def main() -> None:
    test_direct_damage_transition_records_have_resolved_scaling()
    test_expected_transition_scaling_stats_and_metadata()
    test_converter_preserves_transition_scaling_and_source_metadata()
    test_converter_rejects_direct_damage_with_none_scaling()
    print("transition_action_scaling_stat_guard_smoke_test ok")


if __name__ == "__main__":
    main()
