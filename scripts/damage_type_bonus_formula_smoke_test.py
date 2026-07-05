from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.build_profiles import damage_bonus_breakdown
from simulator.models import ActionData, CharacterData
from simulator.simulation import Simulation


def make_character() -> CharacterData:
    return CharacterData(
        id="tester",
        name="Tester",
        resonance_energy=0.0,
        concerto_energy=0.0,
        dmg_bonus=0.2,
        damage_bonuses={
            "all": 0.2,
            "by_category": {"basic_attack": 0.1, "resonance_liberation": 0.6},
            "by_element": {"fusion": 0.3, "generic": 0.05},
        },
    )


def action(action_type: str, tags: list[str] | None = None, damage_bonus_category: str | None = None) -> ActionData:
    return ActionData(
        id=f"test_{action_type}",
        name=f"Test {action_type}",
        character_id="tester",
        action_type=action_type,
        damage_bonus_category=damage_bonus_category,
        duration=1.0,
        cooldown=0.0,
        resonance_energy_cost=0.0,
        damage_multiplier=1.0,
        tags=tags or [],
    )


def assert_close(actual: float, expected: float, message: str) -> None:
    if abs(actual - expected) > 1e-9:
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def test_damage_bonus_buckets() -> None:
    character = make_character()
    basic = damage_bonus_breakdown(character, action("basic_attack", ["fusion"]))
    assert basic["damage_category"] == "basic_attack"
    assert_close(basic["effective_damage_bonus"], 0.2 + 0.1 + 0.3, "basic fusion bonus")

    liberation = damage_bonus_breakdown(character, action("resonance_liberation", ["fusion"]))
    assert liberation["damage_category"] == "resonance_liberation"
    assert_close(liberation["effective_damage_bonus"], 0.2 + 0.6 + 0.3, "liberation fusion bonus")

    skill = damage_bonus_breakdown(character, action("resonance_skill"))
    assert skill["damage_element"] == "generic"
    assert_close(skill["effective_damage_bonus"], 0.2 + 0.05, "generic element fallback")

    skill_as_liberation = damage_bonus_breakdown(
        character,
        action("resonance_skill", damage_bonus_category="resonance_liberation"),
    )
    assert skill_as_liberation["damage_bonus_category"] == "resonance_liberation"
    assert_close(skill_as_liberation["effective_damage_bonus"], 0.2 + 0.6 + 0.05, "skill action using liberation bonus")

    heavy_as_liberation = damage_bonus_breakdown(
        character,
        action("heavy_attack", damage_bonus_category="resonance_liberation"),
    )
    assert heavy_as_liberation["damage_bonus_category"] == "resonance_liberation"
    assert_close(heavy_as_liberation["effective_damage_bonus"], 0.2 + 0.6 + 0.05, "heavy action using liberation bonus")

    future = damage_bonus_breakdown(
        character,
        ActionData(
            id="future_character_skill",
            name="Future Character Skill",
            character_id="dummy_future_character",
            action_type="resonance_skill",
            damage_bonus_category="resonance_liberation",
            duration=1.0,
            cooldown=0.0,
            resonance_energy_cost=0.0,
            damage_multiplier=1.0,
        ),
    )
    assert future["damage_bonus_category"] == "resonance_liberation"
    assert_close(future["effective_damage_bonus"], 0.2 + 0.6 + 0.05, "future character data-driven category")


def test_amp_mechanics_are_not_additive_damage_bonus() -> None:
    sim = Simulation.from_json(PROJECT_ROOT / "data", party="aemeath_mornye_enabled_test_party")
    assert sim.characters["mornye"].build_profile_id == "support_er_component_test"
    assert sim.characters["aemeath"].build_profile_id == "component_test"
    mornye_state = sim.state.character_states["mornye"]
    mornye_state["mode"] = "wide_field_observation"
    mornye_state["wide_field_observation_remaining"] = 10.0
    mornye_state["relative_momentum"] = mornye_state["relative_momentum_cap"]
    assert sim.execute_action("mornye_heavy_attack")
    row = sim.timeline[-1]
    assert row.damage_category == "heavy_attack"
    assert row.category_dmg_bonus == 0.0
    assert row.effective_damage_bonus == row.all_dmg_bonus
    assert row.mornye_interfered_amp == 0.4
    assert row.mornye_interfered_marker_applied is True


if __name__ == "__main__":
    test_damage_bonus_buckets()
    test_amp_mechanics_are_not_additive_damage_bonus()
    print("damage_type_bonus_formula_smoke_test ok")
