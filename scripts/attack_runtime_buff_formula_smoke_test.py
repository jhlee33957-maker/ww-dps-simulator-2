from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.buff_system import apply_buff, buffed_combat_stats
from simulator.build_profiles import apply_attack_components_to_character
from simulator.models import BuffData, CharacterData, CombatState


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert abs(actual - expected) <= tolerance, f"{label}: expected {expected}, got {actual}"


def make_character() -> CharacterData:
    character = CharacterData(
        id="tester",
        name="Tester",
        resonance_energy=0.0,
        concerto_energy=0.0,
        crit_rate=0.0,
        crit_damage=1.0,
    )
    return apply_attack_components_to_character(
        character,
        {
            "character_base_atk": 1000,
            "weapon_base_atk": 500,
            "static_atk_percent": 0.4,
            "static_flat_atk": 200,
            "runtime_atk_percent_bonus": 0.0,
            "runtime_flat_atk_bonus": 0.0,
            "final_attack_reference": 2300,
        },
    )


def test_no_runtime_buff_preserves_static_attack() -> None:
    character = make_character()
    state = CombatState(active_character_id="tester")
    stats = buffed_combat_stats(character, state, {})
    base = 1500
    static = base * 1.4 + 200
    assert_close(stats["runtime_atk_percent_bonus"], 0.0, "default runtime percent")
    assert_close(stats["runtime_flat_atk_bonus"], 0.0, "default runtime flat")
    assert_close(stats["static_attack"], static, "static attack")
    assert_close(stats["effective_attack"], static, "effective attack without buffs")


def test_runtime_percent_and_flat_are_separate() -> None:
    character = make_character()
    state = CombatState(active_character_id="tester")
    percent_buff = BuffData(
        id="runtime_percent",
        name="Runtime Percent",
        duration=10.0,
        modifier_type="attack",
        value=0.2,
        target="active",
    )
    flat_buff = BuffData(
        id="runtime_flat",
        name="Runtime Flat",
        duration=10.0,
        modifier_type="boost",
        value=0.0,
        target="active",
        stat_modifiers={"runtime_flat_atk_bonus": 75.0},
    )
    buffs = {percent_buff.id: percent_buff, flat_buff.id: flat_buff}
    apply_buff(state, percent_buff, "tester")
    apply_buff(state, flat_buff, "tester")
    stats = buffed_combat_stats(character, state, buffs)
    base = 1500
    static = base * 1.4 + 200
    expected = static + base * 0.2 + 75.0
    assert_close(stats["static_atk_percent"], 0.4, "static percent unchanged")
    assert_close(stats["runtime_atk_percent_bonus"], 0.2, "runtime percent")
    assert_close(stats["runtime_flat_atk_bonus"], 75.0, "runtime flat")
    assert_close(stats["effective_attack"], expected, "runtime effective attack")
    assert_close(stats["attack_reference_delta"], static - 2300, "reference uses static attack only")


def main() -> None:
    test_no_runtime_buff_preserves_static_attack()
    test_runtime_percent_and_flat_are_separate()
    print("attack_runtime_buff_formula_smoke_test ok")


if __name__ == "__main__":
    main()
