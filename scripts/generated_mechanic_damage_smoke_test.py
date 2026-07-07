from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from characters.base import CharacterMechanic
from simulator.action_executor import execute_action
from simulator.generated_damage import (
    GeneratedDamagePacket,
    calculate_generated_damage_packet,
    packet_from_mapping,
)
from simulator.models import ActionData, CharacterData, CombatState


class SourceConfirmedGeneratedMechanic(CharacterMechanic):
    def get_generated_damage_packets(
        self,
        state: CombatState,
        action: ActionData,
        *,
        action_time: float,
        combat_time_cost: float,
        combat_start_time: float,
        characters: dict[str, CharacterData],
        buffs: dict[str, Any],
        force_active_buff_ids: set[str],
        mechanic_event_log_fields: dict[str, Any],
        echo_set_log_fields: dict[str, Any],
        weapon_definitions: dict[str, Any],
    ) -> list[GeneratedDamagePacket]:
        return [
            GeneratedDamagePacket(
                id="test_generated_tune_response",
                source_character_id="aemeath",
                source_action_id=action.id,
                name="Test Generated Tune Response",
                formula_type="tune_response",
                damage_element="fusion",
                damage_bonus_category=None,
                scaling_stat="none",
                tune_multiplier=0.25,
                repeat_count=2,
                source_status="workbook_confirmed",
                source_ref="scripts/generated_mechanic_damage_smoke_test.py",
                source_rows=[1],
            )
        ]


def make_state() -> CombatState:
    return CombatState(
        active_character_id="aemeath",
        party_members=["aemeath"],
        resonance_energy={"aemeath": 125.0},
        concerto_energy={"aemeath": 0.0},
        enemy_level=90,
        enemy_res=0.1,
    )


def make_character() -> CharacterData:
    return CharacterData(
        id="aemeath",
        name="Aemeath",
        character_base_atk=1000.0,
        weapon_base_atk=500.0,
        atk_percent=0.2,
        flat_atk=100.0,
        crit_rate=0.5,
        crit_damage=1.5,
        resonance_energy=125.0,
        concerto_energy=0.0,
        attacker_level=90,
        element="fusion",
    )


def make_action() -> ActionData:
    return ActionData(
        id="test_source_action",
        name="Test Source Action",
        character_id="aemeath",
        action_type="resonance_skill",
        duration=1.0,
        action_time=1.0,
        combat_time_cost=1.0,
        cooldown=0.0,
        damage_category="normal",
        damage_multiplier=0.0,
        resonance_energy_cost=0.0,
    )


def test_unresolved_packet_stays_zero() -> None:
    unresolved = packet_from_mapping(
        {
            "id": "unresolved_packet",
            "source_character_id": "aemeath",
            "source_action_id": "test_source_action",
            "name": "Unresolved Packet",
            "formula_type": "tune_response",
            "damage_element": "fusion",
            "scaling_stat": "none",
            "tune_multiplier": 5.0,
            "repeat_count": 10,
            "source_status": "unresolved_no_runtime_effect",
            "source_rows": [2786],
        }
    )
    damage, details = calculate_generated_damage_packet(
        unresolved,
        source_action=make_action(),
        state=make_state(),
        characters={"aemeath": make_character()},
        buffs={},
    )
    assert unresolved.runtime_applicable is False
    assert damage == 0.0
    assert details == []


def test_source_confirmed_normal_packet_is_blocked() -> None:
    normal = GeneratedDamagePacket(
        id="blocked_normal_generated_damage",
        source_character_id="aemeath",
        source_action_id="test_source_action",
        name="Blocked Normal Generated Damage",
        formula_type="normal",
        damage_element="fusion",
        damage_bonus_category="resonance_liberation",
        scaling_stat="atk",
        normal_damage_multiplier=10.0,
        repeat_count=1,
        source_status="workbook_confirmed",
    )
    damage, details = calculate_generated_damage_packet(
        normal,
        source_action=make_action(),
        state=make_state(),
        characters={"aemeath": make_character()},
        buffs={},
    )
    assert normal.runtime_applicable is False
    assert damage == 0.0
    assert details == []


def test_executor_adds_source_confirmed_generated_damage() -> None:
    state = make_state()
    action = make_action()
    result = execute_action(
        action,
        state,
        {"aemeath": make_character()},
        {},
        mechanic=SourceConfirmedGeneratedMechanic(),
        weapon_definitions={},
    )
    assert result.action_id == action.id
    assert result.generated_mechanic_damage > 0.0
    assert result.generated_mechanic_damage_total == result.generated_mechanic_damage
    assert result.generated_mechanic_hit_count == 2
    assert result.damage == result.generated_mechanic_damage
    assert result.total_damage_after == result.generated_mechanic_damage
    assert len(result.generated_mechanic_damage_events) == 1
    event = result.generated_mechanic_damage_events[0]
    assert event["source_action_id"] == action.id
    assert event["source_status"] == "workbook_confirmed"
    assert event["runtime_applicable"] is True
    assert all(hit["is_generated_mechanic_damage"] for hit in result.hit_details)
    assert state.cooldowns == {}
    assert state.resonance_energy["aemeath"] == 125.0


def main() -> None:
    test_unresolved_packet_stays_zero()
    test_source_confirmed_normal_packet_is_blocked()
    test_executor_adds_source_confirmed_generated_damage()
    print("generated_mechanic_damage_smoke_test ok")


if __name__ == "__main__":
    main()
