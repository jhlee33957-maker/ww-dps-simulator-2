from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.build_profiles import (
    calculate_attack_components,
    load_build_profiles,
    resolve_character_build_stats,
)
from simulator.models import CharacterData


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert abs(actual - expected) <= tolerance, f"{label}: expected {expected}, got {actual}"


def test_schema_and_required_profiles() -> None:
    data = load_build_profiles(DATA_DIR)
    assert data["schema_version"] == 2
    profiles = data["profiles"]
    assert "component_test" in profiles["aemeath"]
    assert "support_er_component_test" in profiles["mornye"]
    assert "aemeath_real_manual" in profiles["aemeath"]
    assert "mornye_real_manual" in profiles["mornye"]


def test_component_formula_and_reference_validation_only() -> None:
    result = calculate_attack_components(
        character_base_atk=820,
        weapon_base_atk=560,
        static_atk_percent=0.45,
        static_flat_atk=300,
        runtime_atk_percent_bonus=0.2,
        runtime_flat_atk_bonus=50,
        final_attack_reference=2301,
    )
    base = 820 + 560
    static_attack = base * 1.45 + 300
    effective_attack = static_attack + base * 0.2 + 50
    assert_close(result["base_attack_total"], base, "base_attack_total")
    assert_close(result["static_attack"], static_attack, "static_attack")
    assert_close(result["effective_attack"], effective_attack, "effective_attack")
    assert_close(result["attack_reference_delta"], static_attack - 2301, "reference delta")
    assert_close(result["attack_reference_delta_percent"], (static_attack - 2301) / 2301, "reference delta percent")

    changed_reference = calculate_attack_components(
        character_base_atk=820,
        weapon_base_atk=560,
        static_atk_percent=0.45,
        static_flat_atk=300,
        runtime_atk_percent_bonus=0.2,
        runtime_flat_atk_bonus=50,
        final_attack_reference=9999,
    )
    assert_close(changed_reference["effective_attack"], effective_attack, "reference must not affect damage attack")


def test_energy_regen_default_and_old_aliases() -> None:
    character = CharacterData(id="alias_test", name="Alias Test", resonance_energy=0.0, concerto_energy=0.0)
    data = {
        "schema_version": 2,
        "profiles": {
            "alias_test": {
                "legacy_profile": {
                    "implementation_status": "test_assumption",
                    "atk_percent": 0.5,
                    "flat_atk": 250,
                    "damage_bonus": 0.33,
                    "stat_components": {
                        "character_base_atk": 1000,
                        "weapon_base_atk": 500
                    }
                }
            }
        },
    }
    effective = resolve_character_build_stats(character, "legacy_profile", data)
    assert_close(effective.static_atk_percent, 0.5, "legacy atk_percent")
    assert_close(effective.static_flat_atk, 250, "legacy flat_atk")
    assert_close(effective.damage_bonuses["all"], 0.33, "legacy damage_bonus")
    assert effective.energy_regen == 1.0


def main() -> None:
    test_schema_and_required_profiles()
    test_component_formula_and_reference_validation_only()
    test_energy_regen_default_and_old_aliases()
    print("actual_stat_component_build_profile_smoke_test ok")


if __name__ == "__main__":
    main()
