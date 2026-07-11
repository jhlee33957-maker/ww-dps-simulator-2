from __future__ import annotations

from mornye_syntony_field_heal_test_helpers import execute_to_geopotential, make_sim, scheduled_heals


def main() -> None:
    discord = make_sim()
    execute_to_geopotential(discord)
    heal = scheduled_heals(discord)[0]
    assert heal["applied_weapon_effect_ids"] == []
    assert heal["weapon_effect_triggered"] is False

    starfield = make_sim()
    starfield.characters["mornye"].weapon = {"weapon_id": "starfield_calibrator", "rank": 5}
    before = dict(starfield.state.weapon_effect_trigger_counts)
    execute_to_geopotential(starfield)
    heal = scheduled_heals(starfield)[0]
    assert heal["team_heal_event_emitted"] is True
    assert "heal_party_crit_damage_buff" in heal["applied_weapon_effect_ids"]
    assert heal["weapon_effect_triggered"] is True
    assert heal["starfield_calibrator_party_crit_damage_active"] is True
    assert starfield.state.weapon_effect_trigger_counts != before

    forbidden_team_heal_triggers = [
        log
        for log in starfield.state.weapon_effect_logs
        if log.get("weapon_effect_trigger") == "team_heal"
        and log.get("weapon_effect_event_source") != "scheduled_180f_exact"
    ]
    assert forbidden_team_heal_triggers == []
    print("mornye_syntony_field_heal_starfield_smoke_test ok")


if __name__ == "__main__":
    main()
