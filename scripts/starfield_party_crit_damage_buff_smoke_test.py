from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.buff_system import buffed_combat_stats, tick_buffs
from simulator.weapon_effects import STARFIELD_CALIBRATOR_BUFF_ID, apply_weapon_buff_effects
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def make_sim(*, heal_mode: str = "field_creation_only", rank: int = 1) -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        build_profile_overrides={
            "aemeath": "aemeath_user_real_01",
            "mornye": "mornye_user_real_01",
        },
        transition_config={"mechanics": {"mornye": {"mornye_heal_event_mode": heal_mode}}},
    )
    sim.characters["mornye"].weapon["rank"] = rank
    sim.state.active_character_id = "mornye"
    return sim


def trigger_field_creation_heal(sim: Simulation):
    sim.state.character_states["mornye"]["rest_mass_energy"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    return sim.timeline[-1]


def test_team_heal_applies_party_crit_damage() -> None:
    sim = make_sim()
    before = buffed_combat_stats(sim.characters["aemeath"], sim.state, sim.buffs)
    row = trigger_field_creation_heal(sim)
    after = buffed_combat_stats(sim.characters["aemeath"], sim.state, sim.buffs)
    assert row.team_heal_event_triggered is True
    assert row.weapon_effect_triggered is True
    assert row.weapon_effect_id == "heal_party_crit_damage_buff"
    assert row.weapon_effect_source_status == "user_supplied_weapon_tooltip"
    assert row.weapon_effect_logs
    assert all("weapon_effect_source_status" in log for log in row.weapon_effect_logs)
    assert all("source_status" not in log for log in row.weapon_effect_logs)
    assert row.starfield_calibrator_party_crit_damage_active is True
    assert_close(row.starfield_calibrator_party_crit_damage_bonus, 0.20, "Starfield R1 crit damage buff")
    assert_close(after["crit_damage"], before["crit_damage"] + 0.20, "party crit damage after buff")
    assert_close(after["runtime_crit_damage_bonus"], 0.20, "runtime crit damage bonus")
    assert after["crit_rate"] == before["crit_rate"]

    sim.state.active_character_id = "aemeath"
    sim.state.cooldowns.clear()
    assert sim.execute_action("aemeath_basic_attack")
    buffed_damage = sim.timeline[-1].normal_damage

    clean = make_sim(heal_mode="disabled")
    clean.state.active_character_id = "aemeath"
    assert clean.execute_action("aemeath_basic_attack")
    clean_damage = clean.timeline[-1].normal_damage
    assert buffed_damage > clean_damage

    sim.state.enemy_tune_break_available = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.active_character_id = "aemeath"
    sim.state.cooldowns.clear()
    assert sim.execute_action("aemeath_tune_break")
    tune_row = sim.timeline[-1]
    assert tune_row.tune_break_damage > 0.0
    assert tune_row.runtime_crit_damage_bonus == 0.0 or tune_row.damage_bonus_category == "tune_break"


def test_rank_refresh_expiry_and_disabled_mode() -> None:
    rank5 = make_sim(rank=5)
    row = trigger_field_creation_heal(rank5)
    assert_close(row.starfield_calibrator_party_crit_damage_bonus, 0.40, "Starfield R5 crit damage buff")
    active = [buff for buff in rank5.state.active_buffs if buff.buff_id == STARFIELD_CALIBRATOR_BUFF_ID]
    assert len(active) == 1
    assert active[0].stack_count == 1
    assert_close(row.weapon_effect_duration_seconds, 4.0, "logged duration")
    assert 0.0 < active[0].remaining_duration <= 4.0

    log = apply_weapon_buff_effects(
        trigger="team_heal",
        source_character_id="mornye",
        state=rank5.state,
        characters=rank5.characters,
        buffs=rank5.buffs,
        weapon_definitions=rank5.weapon_definitions,
        application_time=rank5.state.current_time + 1.0,
        event_source="test_refresh",
    )
    assert log["weapon_effect_buff_refreshed"] is True
    assert log["weapon_effect_source_status"] == "user_supplied_weapon_tooltip"
    assert all("source_status" not in entry for entry in log["weapon_effect_logs"])
    active = [buff for buff in rank5.state.active_buffs if buff.buff_id == STARFIELD_CALIBRATOR_BUFF_ID]
    assert len(active) == 1
    assert active[0].stack_count == 1
    assert_close(active[0].remaining_duration, 4.0, "refreshed duration")

    tick_buffs(rank5.state, 4.1)
    assert not any(buff.buff_id == STARFIELD_CALIBRATOR_BUFF_ID for buff in rank5.state.active_buffs)

    disabled = make_sim(heal_mode="disabled")
    row = trigger_field_creation_heal(disabled)
    assert row.team_heal_event_triggered is False
    assert not any(buff.buff_id == STARFIELD_CALIBRATOR_BUFF_ID for buff in disabled.state.active_buffs)


def main() -> None:
    test_team_heal_applies_party_crit_damage()
    test_rank_refresh_expiry_and_disabled_mode()
    print("starfield_party_crit_damage_buff_smoke_test ok")


if __name__ == "__main__":
    main()
