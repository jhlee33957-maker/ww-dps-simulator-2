from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.build_profiles import load_build_profiles, resolve_character_build_stats
from simulator.models import CharacterData
from simulator.weapon_effects import load_weapon_definition


DATA_DIR = ROOT / "data"


def main() -> None:
    weapons_path = DATA_DIR / "weapons.json"
    assert weapons_path.exists()
    data = load_weapon_definition(DATA_DIR)
    weapons = data["weapons"]
    assert "starfield_calibrator" in weapons
    assert "discord" in weapons
    assert "resonance_skill_cast" in data["supported_trigger_event_names"]
    assert "team_heal" in data["supported_trigger_event_names"]
    assert "resource_restore" in data["supported_effect_types"]
    assert "party_stat_buff" in data["supported_effect_types"]

    for weapon_id in ("starfield_calibrator", "discord"):
        for rank in ("1", "2", "3", "4", "5"):
            assert rank in weapons[weapon_id]["rank_values"]
        assert weapons[weapon_id]["effects"]["resonance_skill_concerto_restore"]["resource"] == "concerto_energy"

    profiles = load_build_profiles(DATA_DIR)
    profile = profiles["profiles"]["mornye"]["mornye_user_real_01"]
    weapon = profile["weapon"]
    before_components = json.dumps(profile["stat_components"], sort_keys=True)
    assert weapon["weapon_id"] == "discord"
    assert weapon["rank"] == 5
    assert weapon["static_stats_already_in_profile"] is True
    assert weapon["energy_regen_substat_already_in_profile"] is True
    assert "def_percent_passive_already_in_profile" not in weapon
    assert weapons["discord"]["base_attack_level_90"] == 337
    assert weapons["discord"]["secondary_stat"] == {"type": "energy_regen", "value_level_90": 0.518}
    assert weapons["discord"]["static_stats_already_in_profile_supported"] is True

    characters = json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8-sig"))
    base = CharacterData.model_validate(next(item for item in characters if item["id"] == "mornye"))
    effective = resolve_character_build_stats(base, "mornye_user_real_01", profiles)
    assert effective.weapon["weapon_id"] == "discord"
    assert effective.weapon["rank"] == 5
    assert json.dumps(profile["stat_components"], sort_keys=True) == before_components
    assert effective.static_def_percent == profile["stat_components"]["def"]["percent"]
    assert effective.weapon_base_def == profile["stat_components"]["def"]["weapon_base"]
    assert effective.energy_regen == 2.5424

    damage_formula = (ROOT / "simulator" / "damage_formula.py").read_text(encoding="utf-8")
    tree = ast.parse(damage_formula)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "starfield_calibrator" not in names
    assert "discord" not in names
    weapon_effects_source = (ROOT / "simulator" / "weapon_effects.py").read_text(encoding="utf-8")
    assert '"weapon_effect_source_status": weapon_def.get("source_status")' in weapon_effects_source
    assert '"source_status": weapon_def.get("source_status")' not in weapon_effects_source
    print("weapon_effect_loading_smoke_test ok")


if __name__ == "__main__":
    main()
