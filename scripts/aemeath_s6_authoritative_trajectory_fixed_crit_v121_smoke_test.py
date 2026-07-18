from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.generated_damage import GeneratedDamagePacket, calculate_generated_damage_packet
from simulator.models import ActionData, CharacterData, CombatState


def main() -> None:
    state = CombatState(
        active_character_id="aemeath",
        party_members=["aemeath"],
        resonance_energy={"aemeath": 125.0},
        concerto_energy={"aemeath": 0.0},
        enemy_level=90,
        enemy_res=0.1,
    )
    state.character_mechanics_state["_account_constellation"] = {"aemeath_sequence": 6, "events": []}
    character = CharacterData(
        id="aemeath",
        name="Aemeath",
        attacker_level=90,
        crit_rate=0.10,
        crit_damage=1.50,
        resonance_energy=125.0,
        concerto_energy=0.0,
        account_profile=True,
        sequence=6,
        constellation={"sequence": 6},
    )
    packet = GeneratedDamagePacket(
        id="aemeath_seraphic_duet_tune_rupture_followup",
        source_character_id="aemeath",
        source_action_id="aemeath_heavenfall_finale",
        name="Aemeath Tune Rupture Authoritative Trajectory",
        formula_type="tune_response",
        damage_element="fusion",
        damage_bonus_category="tune_response",
        scaling_stat="none",
        tune_multiplier=1.0,
        source_status="workbook_confirmed",
    )
    action = ActionData(
        id="aemeath_heavenfall_finale",
        name="Aemeath Heavenfall Finale",
        character_id="aemeath",
        action_type="resonance_liberation",
        duration=1.0,
        action_time=1.0,
        combat_time_cost=1.0,
        cooldown=0.0,
        resonance_energy_cost=0.0,
    )
    damage, details = calculate_generated_damage_packet(
        packet,
        source_action=action,
        state=state,
        characters={"aemeath": character},
        buffs={},
    )
    detail = details[0]
    assert detail["override_source"] == "aemeath_s6"
    assert detail["crit_rate_after_override"] == 0.80
    assert detail["crit_damage_after_override"] == 2.75
    assert detail["expected_crit_multiplier"] == 2.40
    assert abs(damage - detail["damage_before_account_fixed_crit"] * 2.40 * 1.40) < 1e-6
    assert any(
        event["event_type"] == "aemeath_s6_fixed_crit_formula"
        for event in detail["account_constellation_damage_context"]
    )
    print("aemeath_s6_authoritative_trajectory_fixed_crit_v121_smoke_test ok")


if __name__ == "__main__":
    main()
