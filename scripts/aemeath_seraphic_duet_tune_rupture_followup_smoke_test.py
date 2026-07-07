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


def make_ready_state(*, enhancement_stacks: int) -> CombatState:
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
    data["forte_enhancement_stacks"] = enhancement_stacks
    data["forte_enhancement_remaining"] = 30.0 if enhancement_stacks else 0.0
    return state


def run_seraphic(*, enhancement_stacks: int):
    mechanic = AemeathMechanic()
    state = make_ready_state(enhancement_stacks=enhancement_stacks)
    result = execute_action(
        load_action("aemeath_seraphic_duet_overturn"),
        state,
        {"aemeath": load_character("aemeath")},
        {},
        mechanic=mechanic,
        weapon_definitions={},
    )
    return state, result


def generated_hits(result) -> list[dict]:
    return [hit for hit in result.hit_details if hit.get("is_generated_mechanic_damage")]


def test_normal_followup_generates_five_tune_response_hits() -> float:
    state, result = run_seraphic(enhancement_stacks=0)
    hits = generated_hits(result)
    assert result.generated_mechanic_damage > 0.0
    assert result.generated_mechanic_damage_total == result.generated_mechanic_damage
    assert result.generated_mechanic_hit_count == 5
    assert result.aemeath_forte_generated_damage == result.generated_mechanic_damage
    assert result.aemeath_forte_generated_damage_total == result.generated_mechanic_damage
    assert result.aemeath_seraphic_duet_followup_triggered is True
    assert result.aemeath_seraphic_duet_followup_damage == result.generated_mechanic_damage
    assert result.aemeath_seraphic_duet_followup_variant == "normal"
    assert result.aemeath_seraphic_duet_followup_repeat_count == 5
    assert result.aemeath_seraphic_duet_followup_multiplier == 1.0935
    assert result.aemeath_seraphic_duet_followup_source_status == "workbook_confirmed"
    assert result.aemeath_forte_enhancement_stacks_consumed == 0
    assert len(hits) == 5
    assert all(hit["formula_type"] == "tune_response" for hit in hits)
    assert all(hit["source_multiplier"] == 1.0935 for hit in hits)
    assert all(hit["source_status"] == "workbook_confirmed" for hit in hits)
    assert all(hit.get("off_tune_value", 0.0) in (0, 0.0, None) for hit in hits)
    assert all(hit.get("everbright_applied") is False for hit in hits)
    assert state.enemy_off_tune_current >= 0.0
    return result.generated_mechanic_damage


def test_enhanced_followup_generates_ten_hits_and_consumes_stack(normal_damage: float) -> None:
    state, result = run_seraphic(enhancement_stacks=2)
    hits = generated_hits(result)
    assert result.generated_mechanic_damage > normal_damage
    assert result.generated_mechanic_damage_total == result.generated_mechanic_damage
    assert result.generated_mechanic_hit_count == 10
    assert result.aemeath_forte_generated_damage == result.generated_mechanic_damage
    assert result.aemeath_forte_generated_damage_total == result.generated_mechanic_damage
    assert result.aemeath_seraphic_duet_followup_triggered is True
    assert result.aemeath_seraphic_duet_followup_damage == result.generated_mechanic_damage
    assert result.aemeath_seraphic_duet_followup_variant == "enhanced"
    assert result.aemeath_seraphic_duet_followup_repeat_count == 10
    assert result.aemeath_seraphic_duet_followup_multiplier == 1.0935
    assert result.aemeath_seraphic_duet_followup_source_status == "workbook_confirmed"
    assert result.aemeath_forte_enhancement_stacks_before == 2
    assert result.aemeath_forte_enhancement_stacks_consumed == 1
    assert result.aemeath_forte_enhancement_stacks_after == 1
    assert state.character_mechanics_state["aemeath"]["forte_enhancement_stacks"] == 1
    assert len(hits) == 10
    assert all(hit["formula_type"] == "tune_response" for hit in hits)
    assert all(hit["source_multiplier"] == 1.0935 for hit in hits)
    assert all(hit.get("everbright_applied") is False for hit in hits)


def test_generated_followup_is_not_policy_or_action() -> None:
    with (ROOT / "data" / "actions.json").open("r", encoding="utf-8-sig") as file:
        action_ids = {raw["id"] for raw in json.load(file)}
    assert "aemeath_seraphic_duet_tune_rupture_followup" not in action_ids
    assert "aemeath_seraphic_duet_tune_rupture_enhanced_followup" not in action_ids


def main() -> None:
    normal_damage = test_normal_followup_generates_five_tune_response_hits()
    test_enhanced_followup_generates_ten_hits_and_consumes_stack(normal_damage)
    test_generated_followup_is_not_policy_or_action()
    print("aemeath_seraphic_duet_tune_rupture_followup_smoke_test ok")


if __name__ == "__main__":
    main()
