from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.build_profiles import action_damage_bonus_category, damage_bonus_breakdown
from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
ECHO_ACTION_IDS = [
    "mornye_echo_reactor_husk",
    "aemeath_echo_sigillum_hit_1",
    "aemeath_echo_sigillum_hit_2",
    "lynae_echo_hyvatia",
]


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def character_with_echo_bonus(sim: Simulation, character_id: str, value: float):
    character = sim.characters[character_id].model_copy(deep=True)
    bonuses = dict(character.damage_bonuses or {})
    by_category = dict((bonuses.get("by_category") or {}))
    by_category["echo_ability"] = value
    bonuses["by_category"] = by_category
    character.damage_bonuses = bonuses
    return character


def test_breakdown_category() -> None:
    sim = Simulation.from_json("data", selected_character_ids=PARTY_ID, initial_active_character="mornye")
    for action_id in ECHO_ACTION_IDS + ["aemeath_echo_sigillum"]:
        action = sim.actions[action_id]
        assert action_damage_bonus_category(action) == "echo_ability"
        character = sim.characters[action.character_id]
        baseline = damage_bonus_breakdown(character, action)
        boosted = damage_bonus_breakdown(character_with_echo_bonus(sim, action.character_id, 0.25), action)
        assert baseline["damage_bonus_category"] == "echo_ability"
        assert boosted["damage_bonus_category"] == "echo_ability"
        assert_close(boosted["category_dmg_bonus"], 0.25, f"{action_id} category bonus")
        assert_close(
            boosted["effective_damage_bonus"] - baseline["effective_damage_bonus"],
            0.25,
            f"{action_id} effective bonus delta",
        )


def test_runtime_logs() -> None:
    reactor = Simulation.from_json("data", selected_character_ids=PARTY_ID, initial_active_character="mornye")
    assert reactor.execute_action("mornye_echo_reactor_husk")
    assert reactor.timeline[-1].damage_bonus_category == "echo_ability"
    assert reactor.timeline[-1].hit_details[0]["damage_bonus_category"] == "echo_ability"

    sigillum = Simulation.from_json("data", selected_character_ids=PARTY_ID, initial_active_character="aemeath")
    assert sigillum.execute_action("aemeath_echo_sigillum")
    assert sigillum.execute_action("short_wait")
    assert sigillum.execute_action("short_wait")
    events = [
        event
        for row in sigillum.timeline
        for event in row.scheduled_damage_events
        if event.get("source_action_id") == "aemeath_echo_sigillum"
    ]
    assert [event["hit_index"] for event in events] == [1, 2]
    assert all(event["damage_bonus_category"] == "echo_ability" for event in events)
    assert all(event["hit_details"][0]["damage_bonus_category"] == "echo_ability" for event in events)

    hyvatia = Simulation.from_json("data", selected_character_ids=PARTY_ID, initial_active_character="lynae")
    assert hyvatia.execute_action("lynae_echo_hyvatia")
    assert hyvatia.timeline[-1].damage_bonus_category == "echo_ability"
    assert all(detail["damage_bonus_category"] == "echo_ability" for detail in hyvatia.timeline[-1].hit_details)


def main() -> None:
    test_breakdown_category()
    test_runtime_logs()
    print("echo_ability_damage_category_runtime_smoke_test ok")


if __name__ == "__main__":
    main()
