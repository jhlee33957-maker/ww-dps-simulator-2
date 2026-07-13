from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

STATUS_BY_TYPE = {
    "single": "workbook_confirmed",
    "sum_rows": "workbook_confirmed_summed_from_rows",
    "repeat_aware": "workbook_confirmed_repeat_aware",
    "mutually_exclusive_timing_variant": "workbook_confirmed_mode_representative",
    "mutually_exclusive_mode_variant": "workbook_confirmed_mode_representative",
    "repeat_aware_mode_variant": "workbook_confirmed_repeat_aware_mode_variant",
    "constellation_same_action_rows": "workbook_confirmed_internal_alias",
    "workbook_confirmed_zero": "workbook_confirmed_zero",
    "non_damaging_selector": "non_damaging_selector",
    "unresolved_echo_off_tune": "unresolved_echo_off_tune",
}
ALIASES = {
    "lynae_polychrome_leap_stage_1_c1": "lynae_polychrome_leap_stage_1",
    "lynae_polychrome_leap_stage_2_c1": "lynae_polychrome_leap_stage_2",
    "lynae_polychrome_leap_stage_3_c1": "lynae_polychrome_leap_stage_3",
    "lynae_iridescent_splash_c3": "lynae_iridescent_splash",
    "lynae_visual_impact_c3": "lynae_visual_impact",
    "lynae_resonance_liberation_prismatic_overblast_c5": (
        "lynae_resonance_liberation_prismatic_overblast"
    ),
}
ALIAS_NOTE = "Constellation changes the damage option but uses the same action-row Off-Tune value as the C0 action."
UNRESOLVED_ID = "lynae_echo_hyvatia"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert abs(float(actual) - float(expected)) <= tolerance, f"{label}: expected {expected}, got {actual}"


def main() -> None:
    mapping_path = ROOT / "data/source/lynae_off_tune_direct_mapping_v80.json"
    mapping = read_json(mapping_path)
    mappings = mapping["mappings"]
    assert len(mappings) == 43
    assert mapping["action_record_count"] == 43
    assert mapping["confirmed_source_backed_action_count"] == 37
    assert mapping["confirmed_selector_count"] == 5
    assert mapping["unresolved_count"] == 1
    assert [item["action_id"] for item in mappings if item["confidence"] == "unresolved"] == [UNRESOLVED_ID]

    actions = {action["id"]: action for action in read_json(ROOT / "data/actions.json")}
    transitions = {action["id"]: action for action in read_json(ROOT / "data/transition_actions.json")}
    for item in mappings:
        action_id = item["action_id"]
        action = actions[action_id]
        expected_status = STATUS_BY_TYPE[item["mapping_type"]]
        expected_value = 0.0 if action_id == UNRESOLVED_ID else float(item["off_tune_value"])
        assert_close(action["off_tune_value"], expected_value, f"{action_id} Off-Tune")
        assert action["off_tune_value_source_status"] == expected_status
        assert action.get("off_tune_value_source_ref") == item.get("source_ref")

        alias_of = ALIASES.get(action_id)
        if alias_of is None:
            assert action.get("off_tune_value_alias_of") is None
            assert action.get("off_tune_value_alias_note") is None
        else:
            assert action.get("off_tune_value_alias_of") == alias_of
            assert action.get("off_tune_value_alias_note") == ALIAS_NOTE

    hyvatia = actions[UNRESOLVED_ID]
    assert hyvatia["off_tune_value"] == 0.0
    assert hyvatia["off_tune_value_source_status"] == "unresolved_echo_off_tune"
    assert hyvatia["off_tune_value_source_ref"] == "声骸!371"

    selector_ids = {
        item["action_id"]
        for item in mappings
        if item["mapping_type"] == "non_damaging_selector"
    }
    assert selector_ids == {
        "lynae_basic_attack",
        "lynae_spark_collision",
        "lynae_resonance_skill",
        "lynae_resonance_liberation",
        "lynae_polychrome_leap",
    }
    for action_id in selector_ids:
        assert actions[action_id]["off_tune_value"] == 0.0
        assert actions[action_id]["off_tune_value_source_status"] == "non_damaging_selector"

    intro_action = actions["lynae_intro_time_to_show_some_colors"]
    intro_transition = transitions["lynae_intro_time_to_show_some_colors"]
    assert_close(intro_transition["off_tune_value"], intro_action["off_tune_value"], "intro transition Off-Tune")
    assert intro_transition["off_tune_value_source_status"] == intro_action["off_tune_value_source_status"]
    assert intro_transition["off_tune_value_source_ref"] == intro_action["off_tune_value_source_ref"]

    print("lynae_off_tune_direct_mapping_smoke_test ok")


if __name__ == "__main__":
    main()
