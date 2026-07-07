from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from characters.aemeath import AemeathMechanic
from simulator.action_executor import execute_action
from simulator.models import ActionData, CharacterData, CombatState


def load_action(action_id: str) -> ActionData:
    with (ROOT / "data" / "actions.json").open("r", encoding="utf-8-sig") as file:
        for raw in json.load(file):
            if raw["id"] == action_id:
                return ActionData(**raw)
    raise AssertionError(f"missing action {action_id}")


def load_character(character_id: str) -> CharacterData:
    with (ROOT / "data" / "characters.json").open("r", encoding="utf-8-sig") as file:
        for raw in json.load(file):
            if raw["id"] == character_id:
                return CharacterData(**raw)
    raise AssertionError(f"missing character {character_id}")


def make_state() -> CombatState:
    return CombatState(
        active_character_id="aemeath",
        party_members=["aemeath"],
        resonance_energy={"aemeath": 125.0},
        concerto_energy={"aemeath": 0.0},
        mechanics_config={"aemeath": {"aemeath_resonance_mode": "tune_rupture"}},
    )


def test_overdrive_grants_forte_enhancement_and_trail_no_cost() -> None:
    mechanic = AemeathMechanic()
    state = make_state()
    action = load_action("aemeath_liberation_overdrive")
    result = execute_action(
        action,
        state,
        {"aemeath": load_character("aemeath")},
        {},
        mechanic=mechanic,
        weapon_definitions={},
    )
    assert result.valid
    mechanic.after_action(state, action, result)
    data = state.character_mechanics_state["aemeath"]
    assert data["forte_enhancement_stacks"] == 2
    assert data["forte_enhancement_remaining"] == 30.0
    assert data["forte_enhancement_max_stacks"] == 2
    assert data["trail_no_cost_remaining"] == 30.0
    assert data["stardust_resonance_remaining"] == 30.0
    assert data["synchronization_rate"] == 30.0
    assert data["resonance_rate"] == 1.0

    mechanic.advance_time(state, 10.0)
    assert data["forte_enhancement_stacks"] == 2
    assert data["forte_enhancement_remaining"] == 20.0
    assert data["trail_no_cost_remaining"] == 20.0
    mechanic.advance_time(state, 20.0)
    assert data["forte_enhancement_stacks"] == 0
    assert data["forte_enhancement_remaining"] == 0.0
    assert data["trail_no_cost_remaining"] == 0.0


def test_seraphic_duet_consumes_one_enhancement_stack_and_trail_no_cost() -> None:
    mechanic = AemeathMechanic()
    state = make_state()
    mechanic.initialize_state(state)
    data = state.character_mechanics_state["aemeath"]
    data.update(
        {
            "form": "aemeath",
            "synchronization_rate": 100.0,
            "seraphic_duo_remaining": 5.0,
            "forte_enhancement_stacks": 2,
            "forte_enhancement_remaining": 30.0,
            "trail_no_cost_remaining": 30.0,
            "rupturous_trail_stacks": 3,
            "rupturous_trail_remaining": 30.0,
        }
    )
    result = execute_action(
        load_action("aemeath_seraphic_duet_overturn"),
        state,
        {"aemeath": load_character("aemeath")},
        {},
        mechanic=mechanic,
        weapon_definitions={},
    )
    assert result.aemeath_seraphic_duet_followup_variant == "enhanced"
    assert result.aemeath_forte_enhancement_stacks_before == 2
    assert result.aemeath_forte_enhancement_stacks_consumed == 1
    assert result.aemeath_forte_enhancement_stacks_after == 1
    assert result.aemeath_trail_no_cost_consumed is True
    assert data["forte_enhancement_stacks"] == 1
    assert data["trail_no_cost_remaining"] == 0.0
    assert data["rupturous_trail_stacks"] == 3


def main() -> None:
    test_overdrive_grants_forte_enhancement_and_trail_no_cost()
    test_seraphic_duet_consumes_one_enhancement_stack_and_trail_no_cost()
    print("aemeath_overdrive_forte_enhancement_state_smoke_test ok")


if __name__ == "__main__":
    main()
