from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.buff_system import apply_buff
from simulator.build_profiles import apply_attack_components_to_character
from simulator.damage_formula import expected_damage
from simulator.models import ActionData, BuffData, CharacterData, CombatState


def make_character(
    *,
    static_atk_percent: float = 0.4,
    static_flat_atk: float = 200.0,
    runtime_atk_percent_bonus: float = 0.0,
    final_attack_reference: float | None = None,
) -> CharacterData:
    character = CharacterData(
        id="tester",
        name="Tester",
        resonance_energy=0.0,
        concerto_energy=0.0,
        crit_rate=0.0,
        crit_damage=1.0,
        damage_bonuses={
            "all": 0.1,
            "by_category": {"resonance_liberation": 0.5},
            "by_element": {"fusion": 0.2},
        },
    )
    return apply_attack_components_to_character(
        character,
        {
            "character_base_atk": 1000,
            "weapon_base_atk": 500,
            "static_atk_percent": static_atk_percent,
            "static_flat_atk": static_flat_atk,
            "runtime_atk_percent_bonus": runtime_atk_percent_bonus,
            "runtime_flat_atk_bonus": 0.0,
            "final_attack_reference": final_attack_reference,
        },
    )


def make_action() -> ActionData:
    return ActionData(
        id="test_liberation",
        name="Test Liberation",
        character_id="tester",
        action_type="resonance_skill",
        damage_bonus_category="resonance_liberation",
        duration=1.0,
        cooldown=0.0,
        resonance_energy_cost=0.0,
        damage_multiplier=1.0,
        tags=["fusion"],
    )


def damage(character: CharacterData, buffs: dict[str, BuffData] | None = None, state: CombatState | None = None) -> float:
    return expected_damage(character, make_action(), state or CombatState(active_character_id="tester"), buffs or {})


def test_effective_attack_drives_damage() -> None:
    baseline = damage(make_character())
    more_percent = damage(make_character(static_atk_percent=0.6))
    more_flat = damage(make_character(static_flat_atk=350.0))
    runtime_percent = damage(make_character(runtime_atk_percent_bonus=0.2))
    reference_only = damage(make_character(final_attack_reference=9999.0))
    assert more_percent > baseline
    assert more_flat > baseline
    assert runtime_percent > baseline
    assert abs(reference_only - baseline) <= 1e-9


def test_runtime_buff_and_category_bonus_still_work() -> None:
    character = make_character()
    state = CombatState(active_character_id="tester")
    buff = BuffData(
        id="atk_runtime",
        name="Runtime ATK",
        duration=10.0,
        modifier_type="attack",
        value=0.2,
        target="active",
    )
    apply_buff(state, buff, "tester")
    buffed = damage(character, {buff.id: buff}, state)
    unbuffed = damage(character)
    assert buffed > unbuffed

    action_without_category = make_action()
    action_without_category.damage_bonus_category = "resonance_skill"
    no_liberation_bonus = expected_damage(character, action_without_category, CombatState(active_character_id="tester"), {})
    assert unbuffed > no_liberation_bonus


def main() -> None:
    test_effective_attack_drives_damage()
    test_runtime_buff_and_category_bonus_still_work()
    print("damage_formula_effective_attack_smoke_test ok")


if __name__ == "__main__":
    main()
