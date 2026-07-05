from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.build_profiles import (
    apply_scaling_components_to_character,
    calculate_scaling_stat_components,
    resolve_character_build_stats,
)
from simulator.models import CharacterData


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert abs(actual - expected) <= tolerance, f"{label}: expected {expected}, got {actual}"


def test_generic_components_and_reference_validation_only() -> None:
    result = calculate_scaling_stat_components(
        {
            "atk": {"character_base": 1000, "weapon_base": 500, "percent": 0.4, "flat": 200, "final_reference": 2300},
            "def": {"character_base": 800, "weapon_base": 0, "percent": 0.5, "flat": 120, "final_reference": 1320},
            "hp": {"character_base": 10000, "weapon_base": 0, "percent": 0.3, "flat": 1000, "final_reference": 14000},
        },
        {
            "atk": {"percent": 0.2, "flat": 50},
            "def": {"percent": 0.1, "flat": 30},
            "hp": {"percent": 0.05, "flat": 500},
        },
    )
    assert_close(result["atk"]["effective_value"], (1500 * 1.4 + 200) + 1500 * 0.2 + 50, "effective atk")
    assert_close(result["def"]["effective_value"], (800 * 1.5 + 120) + 800 * 0.1 + 30, "effective def")
    assert_close(result["hp"]["effective_value"], (10000 * 1.3 + 1000) + 10000 * 0.05 + 500, "effective hp")
    changed_reference = calculate_scaling_stat_components(
        {"def": {"character_base": 800, "weapon_base": 0, "percent": 0.5, "flat": 120, "final_reference": 9999}}
    )
    assert_close(changed_reference["def"]["effective_value"], 800 * 1.5 + 120, "reference validation only")


def test_legacy_aliases_and_effective_attack_alias() -> None:
    character = CharacterData(id="alias_test", name="Alias Test", resonance_energy=0.0, concerto_energy=0.0)
    effective = resolve_character_build_stats(
        character,
        "legacy_profile",
        {
            "schema_version": 3,
            "profiles": {
                "alias_test": {
                    "legacy_profile": {
                        "implementation_status": "test_assumption",
                        "stat_components": {
                            "character_base_atk": 1000,
                            "weapon_base_atk": 500,
                        },
                        "atk_percent": 0.5,
                        "flat_atk": 250,
                        "damage_bonus": 0.33,
                    }
                }
            },
        },
    )
    assert_close(effective.effective_atk, 1500 * 1.5 + 250, "effective_atk")
    assert_close(effective.effective_attack, effective.effective_atk, "effective_attack compatibility")
    assert_close(effective.damage_bonuses["all"], 0.33, "legacy damage bonus")
    assert effective.energy_regen == 1.0


def test_apply_scaling_components_to_character() -> None:
    character = CharacterData(id="tester", name="Tester", resonance_energy=0.0, concerto_energy=0.0)
    apply_scaling_components_to_character(
        character,
        {
            "atk": {"character_base": 100, "weapon_base": 50, "percent": 0.1, "flat": 5},
            "def": {"character_base": 200, "weapon_base": 0, "percent": 0.2, "flat": 10},
            "hp": {"character_base": 1000, "weapon_base": 0, "percent": 0.3, "flat": 100},
        },
    )
    assert_close(character.effective_atk, 170.0, "character atk")
    assert_close(character.effective_def, 250.0, "character def")
    assert_close(character.effective_hp, 1400.0, "character hp")


def main() -> None:
    test_generic_components_and_reference_validation_only()
    test_legacy_aliases_and_effective_attack_alias()
    test_apply_scaling_components_to_character()
    print("generic_scaling_stat_component_smoke_test ok")


if __name__ == "__main__":
    main()
