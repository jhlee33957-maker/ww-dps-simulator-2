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


def make_ready_state(*, stardust: bool = False) -> CombatState:
    state = CombatState(
        active_character_id="aemeath",
        party_members=["aemeath"],
        resonance_energy={"aemeath": 125.0},
        concerto_energy={"aemeath": 0.0},
        mechanics_config={"aemeath": {"aemeath_resonance_mode": "tune_rupture"}},
    )
    mechanic = AemeathMechanic()
    mechanic.initialize_state(state)
    data = state.character_mechanics_state["aemeath"]
    data["form"] = "aemeath"
    data["synchronization_rate"] = 100.0
    data["seraphic_duo_remaining"] = 5.0
    data["stardust_resonance_remaining"] = 30.0 if stardust else 0.0
    return state


def test_seraphic_duet_followup_is_source_confirmed_damage() -> None:
    mechanic = AemeathMechanic()
    state = make_ready_state()
    result = execute_action(
        load_action("aemeath_seraphic_duet_overturn"),
        state,
        {"aemeath": load_character("aemeath")},
        {},
        mechanic=mechanic,
        weapon_definitions={},
    )
    assert result.normal_damage > 0.0
    assert result.generated_mechanic_damage > 0.0
    assert result.generated_mechanic_hit_count == 5
    assert result.aemeath_seraphic_duet_followup_triggered is True
    assert result.aemeath_seraphic_duet_followup_damage == result.generated_mechanic_damage
    assert result.aemeath_seraphic_duet_followup_source_status == "workbook_confirmed"
    assert result.aemeath_seraphic_duet_followup_mode == "tune_rupture"
    assert result.aemeath_seraphic_duet_followup_variant == "normal"
    assert result.aemeath_seraphic_duet_followup_repeat_count == 5
    assert result.aemeath_seraphic_duet_followup_multiplier == 1.0935
    assert result.aemeath_seraphic_duet_followup_source_rows == [2578, 2628, 2786, 2931]
    assert result.aemeath_stardust_resonance_active_for_followup is False
    assert len(result.generated_mechanic_damage_events) == 1
    event = result.generated_mechanic_damage_events[0]
    assert event["source_action_id"] == "aemeath_seraphic_duet_overturn"
    assert event["source_status"] == "workbook_confirmed"
    assert event["runtime_applicable"] is True
    assert event["repeat_count"] == 5
    assert event["source_multiplier"] == 1.0935
    assert event["source_rows"] == [2786, 2931, 2578, 2628]
    assert any(hit.get("is_generated_mechanic_damage") for hit in result.hit_details)


def test_stardust_does_not_select_enhanced_followup_by_itself() -> None:
    mechanic = AemeathMechanic()
    state = make_ready_state(stardust=True)
    result = execute_action(
        load_action("aemeath_seraphic_duet_overturn"),
        state,
        {"aemeath": load_character("aemeath")},
        {},
        mechanic=mechanic,
        weapon_definitions={},
    )
    with (ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json").open(
        "r", encoding="utf-8-sig"
    ) as file:
        config = json.load(file)
    enhanced = [item for item in config["modes"]["tune_rupture"]["seraphic_duet_followups"] if item["variant"] == "enhanced"][0]
    assert enhanced["repeat_count"] == 10
    assert result.aemeath_stardust_resonance_active_for_followup is True
    assert result.generated_mechanic_damage > 0.0
    assert result.aemeath_seraphic_duet_followup_variant == "normal"
    assert result.aemeath_seraphic_duet_followup_repeat_count == 5
    assert result.aemeath_seraphic_duet_followup_source_status == "workbook_confirmed"


def main() -> None:
    test_seraphic_duet_followup_is_source_confirmed_damage()
    test_stardust_does_not_select_enhanced_followup_by_itself()
    print("aemeath_seraphic_duet_followup_smoke_test ok")


if __name__ == "__main__":
    main()
