from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"
TRANSITION_ACTIONS_PATH = DATA_DIR / "transition_actions.json"

EXPECTED_METADATA = {
    "aemeath_qte_intro_human": {
        "raw_skill_category": "\u53d8\u594f",
        "raw_damage_type": "\u53d8\u594f\u4f24\u5bb3",
        "state_name_raw": "\u6d41\u5149\u589e\u5e45\u72b6\u6001",
    },
    "aemeath_qte_intro_mech": {
        "raw_skill_category": "\u5171\u9e23\u6280\u80fd",
        "raw_damage_type": "\u53d8\u594f\u4f24\u5bb3",
        "state_name_raw": "\u6d41\u5149\u589e\u5e45\u72b6\u6001",
    },
}

EXPECTED_FUNCTIONAL_VALUES = {
    "aemeath_qte_intro_human": {
        "action_time": 1.0,
        "combat_time_cost": 0.1667,
        "hits": [0.1346, 0.1346, 1.0766],
        "damage_bonus_category": "none_or_unmodeled_intro",
    },
    "aemeath_qte_intro_mech": {
        "action_time": 1.2,
        "combat_time_cost": 0.4333,
        "hits": [0.653, 0.9795],
        "damage_bonus_category": "resonance_skill",
    },
}

MOJIBAKE_MARKERS = ("?", "\ufffd", "\u5360", "\ucc26", "\uca4d", "\ucc59", "\ucc57")


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-4) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def contains_hangul(value: str) -> bool:
    return any("\uac00" <= char <= "\ud7a3" for char in value)


def metadata_values(record: dict[str, Any]) -> dict[str, str]:
    metadata = record["metadata"]
    flow_light = metadata["flow_light_state_grant_review_only"]
    return {
        "raw_skill_category": metadata["raw_skill_category"],
        "raw_damage_type": metadata["raw_damage_type"],
        "state_name_raw": flow_light["state_name_raw"],
    }


def load_transition_actions() -> dict[str, dict[str, Any]]:
    with TRANSITION_ACTIONS_PATH.open(encoding="utf-8") as handle:
        records = json.load(handle)
    return {record["id"]: record for record in records}


def test_metadata_decodes_to_expected_unicode() -> None:
    records = load_transition_actions()

    for action_id, expected in EXPECTED_METADATA.items():
        assert action_id in records, f"missing transition action: {action_id}"
        actual = metadata_values(records[action_id])
        assert actual == expected, f"{action_id} metadata mismatch: {actual}"


def test_metadata_has_no_obvious_mojibake() -> None:
    records = load_transition_actions()

    for action_id in EXPECTED_METADATA:
        for field_name, value in metadata_values(records[action_id]).items():
            assert isinstance(value, str), f"{action_id}.{field_name} is not a string"
            assert not contains_hangul(value), f"{action_id}.{field_name} contains Hangul mojibake: {value!r}"
            for marker in MOJIBAKE_MARKERS:
                assert marker not in value, f"{action_id}.{field_name} contains mojibake marker {marker!r}: {value!r}"


def test_functional_values_remain_unchanged() -> None:
    records = load_transition_actions()

    for action_id, expected in EXPECTED_FUNCTIONAL_VALUES.items():
        record = records[action_id]
        assert_close(record["action_time"], expected["action_time"], f"{action_id} action_time")
        assert_close(record["combat_time_cost"], expected["combat_time_cost"], f"{action_id} combat_time_cost")
        assert record["damage_bonus_category"] == expected["damage_bonus_category"]
        assert len(record["hits"]) == len(expected["hits"])
        for index, expected_hit in enumerate(expected["hits"]):
            assert_close(record["hits"][index], expected_hit, f"{action_id} hit {index}")


def test_transition_actions_remain_non_policy() -> None:
    action_ids = set(EXPECTED_METADATA)

    for party in ("aemeath", "aemeath_test_party"):
        sim = Simulation.from_json(DATA_DIR, party=party)
        policy_ids = set(sim.get_policy_action_ids())
        assert action_ids.isdisjoint(policy_ids), f"{party} exposes transition actions as policy actions"
        assert {f"transition:{action_id}" for action_id in action_ids}.isdisjoint(policy_ids), (
            f"{party} exposes internal transition action ids as policy actions"
        )


def main() -> None:
    test_metadata_decodes_to_expected_unicode()
    test_metadata_has_no_obvious_mojibake()
    test_functional_values_remain_unchanged()
    test_transition_actions_remain_non_policy()
    print("Transition action metadata encoding smoke test passed.")


if __name__ == "__main__":
    main()
