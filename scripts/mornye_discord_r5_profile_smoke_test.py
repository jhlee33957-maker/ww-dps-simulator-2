from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.build_profiles import load_build_profiles, resolve_character_build_stats
from simulator.models import CharacterData
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=tol), f"{label}: expected {expected}, got {actual}"


def test_profile_values() -> None:
    profiles = load_build_profiles(DATA_DIR)
    profile = profiles["profiles"]["mornye"]["mornye_user_real_01"]
    weapon = profile["weapon"]
    assert weapon["weapon_id"] == "discord"
    assert weapon["rank"] == 5
    assert weapon["static_stats_already_in_profile"] is True
    assert weapon["energy_regen_substat_already_in_profile"] is True
    assert "def_percent_passive_already_in_profile" not in weapon
    assert "Starfield Calibrator DEF passive" in weapon["notes"]
    assert "party Crit DMG buff" in weapon["notes"]

    stat_def = profile["stat_components"]["def"]
    assert_close(stat_def["percent"], 1.0406, "DEF percent")
    assert_close(stat_def["final_reference"], 2997.0536, "final DEF")
    assert_close(profile["combat_stats"]["energy_regen"], 2.5424, "Energy Regen")

    characters = json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8-sig"))
    base = CharacterData.model_validate(next(item for item in characters if item["id"] == "mornye"))
    effective = resolve_character_build_stats(base, "mornye_user_real_01", profiles)
    assert effective.weapon["weapon_id"] == "discord"
    assert effective.weapon["rank"] == 5
    assert_close(effective.static_def_percent, 1.0406, "effective DEF percent")
    assert_close(effective.final_def_reference, 2997.0536, "effective final DEF")
    assert_close(effective.energy_regen, 2.5424, "effective Energy Regen")


def test_discord_weapon_definition_metadata() -> None:
    weapons = json.loads((DATA_DIR / "weapons.json").read_text(encoding="utf-8-sig"))["weapons"]
    discord = weapons["discord"]
    assert discord["base_attack_level_90"] == 337
    assert discord["secondary_stat"] == {"type": "energy_regen", "value_level_90": 0.518}
    assert discord["static_stats_already_in_profile_supported"] is True
    assert [discord["rank_values"][str(rank)]["concerto_restore_on_resonance_skill"] for rank in range(1, 6)] == [
        8.0,
        10.0,
        12.0,
        14.0,
        16.0,
    ]
    effect = discord["effects"]["resonance_skill_concerto_restore"]
    assert effect["trigger"] == "resonance_skill_cast"
    assert effect["resource"] == "concerto_energy"
    assert effect["cooldown_seconds"] == 20.0


def test_interfered_marker_uses_discord_energy_regen() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_lynae_enabled_test_party", initial_active_character="mornye")
    assert_close(sim.characters["mornye"].energy_regen, 2.5424, "Mornye ER")
    state = sim.state.character_mechanics_state["mornye"]
    state["mode"] = "wide_field_observation"
    state["relative_momentum"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")

    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0
    assert sim.execute_action("mornye_tune_break")
    row = sim.timeline[-1]
    assert row.mornye_interfered_marker_applied is True
    assert_close(row.interfered_marker_damage_taken_amp, 0.3856, "Interfered Marker amp")
    assert_close(sim.state.interfered_marker_remaining, 8.0, "Interfered Marker duration")


def test_discord_does_not_apply_starfield_effects() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_lynae_enabled_test_party", initial_active_character="mornye")
    sim.state.character_mechanics_state["mornye"]["rest_mass_energy"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    row = sim.timeline[-1]
    assert sim.characters["mornye"].weapon["weapon_id"] == "discord"
    assert row.weapon_effect_id != "heal_party_crit_damage_buff"
    assert row.starfield_calibrator_party_crit_damage_active is False
    assert not any(buff.buff_id == "starfield_calibrator_party_crit_damage" for buff in sim.state.active_buffs)


def main() -> None:
    test_profile_values()
    test_discord_weapon_definition_metadata()
    test_interfered_marker_uses_discord_energy_regen()
    test_discord_does_not_apply_starfield_effects()
    print("mornye_discord_r5_profile_smoke_test ok")


if __name__ == "__main__":
    main()
