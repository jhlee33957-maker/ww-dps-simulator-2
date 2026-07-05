from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.build_profiles import apply_scaling_components_to_character
from simulator.damage_formula import expected_damage
from simulator.models import ActionData, CharacterData, CombatState


def make_character(*, atk: float = 1000.0, defense: float = 2000.0, hp: float = 10000.0) -> CharacterData:
    character = CharacterData(
        id="dummy_future_character",
        name="Dummy Future Character",
        resonance_energy=0.0,
        concerto_energy=0.0,
        crit_rate=0.0,
        crit_damage=1.0,
        damage_bonuses={"all": 0.1, "by_category": {"resonance_liberation": 0.5}, "by_element": {}},
    )
    return apply_scaling_components_to_character(
        character,
        {
            "atk": {"character_base": atk, "weapon_base": 0, "percent": 0, "flat": 0},
            "def": {"character_base": defense, "weapon_base": 0, "percent": 0, "flat": 0},
            "hp": {"character_base": hp, "weapon_base": 0, "percent": 0, "flat": 0},
        },
    )


def make_action(action_id: str, scaling_stat: str) -> ActionData:
    return ActionData(
        id=action_id,
        name=action_id,
        character_id="dummy_future_character",
        action_type="resonance_skill",
        damage_bonus_category="resonance_liberation",
        scaling_stat=scaling_stat,
        duration=1.0,
        cooldown=0.0,
        resonance_energy_cost=0.0,
        damage_multiplier=1.0,
    )


def damage(character: CharacterData, scaling_stat: str) -> float:
    return expected_damage(character, make_action(f"{scaling_stat}_action", scaling_stat), CombatState(active_character_id=character.id), {})


def test_scaling_stat_selects_base_value() -> None:
    baseline = make_character()
    more_def = make_character(defense=3000.0)
    more_atk = make_character(atk=2000.0)
    more_hp = make_character(hp=12000.0)

    assert damage(more_atk, "atk") > damage(baseline, "atk")
    assert damage(more_def, "def") > damage(baseline, "def")
    assert damage(more_hp, "hp") > damage(baseline, "hp")
    assert abs(damage(more_def, "atk") - damage(baseline, "atk")) <= 1e-9
    assert abs(damage(more_atk, "def") - damage(baseline, "def")) <= 1e-9


def test_damage_bonus_category_independent_from_scaling_stat() -> None:
    character = make_character()
    with_liberation_bonus = damage(character, "def")
    action = make_action("def_skill_bonus", "def")
    action.damage_bonus_category = "resonance_skill"
    without_liberation_bonus = expected_damage(character, action, CombatState(active_character_id=character.id), {})
    assert with_liberation_bonus > without_liberation_bonus


def main() -> None:
    test_scaling_stat_selects_base_value()
    test_damage_bonus_category_independent_from_scaling_stat()
    print("action_scaling_stat_damage_formula_smoke_test ok")


if __name__ == "__main__":
    main()
