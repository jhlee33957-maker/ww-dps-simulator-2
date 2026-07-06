from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.build_profiles import load_build_profiles, resolve_character_build_stats
from simulator.models import CharacterData
from simulator.weapon_effects import load_weapon_definition


DATA_DIR = ROOT / "data"


def main() -> None:
    weapons = load_weapon_definition(DATA_DIR)
    everbright = weapons["weapons"]["everbright_polestar"]
    assert everbright["display_name"] == "Everbright Polestar"
    assert "mechanic_event_emitted" in weapons["supported_trigger_event_names"]
    assert "conditional_penetration_buff" in weapons["supported_effect_types"]
    for rank, expected in {
        "1": (0.12, 0.32, 0.10),
        "2": (0.15, 0.40, 0.15),
        "3": (0.18, 0.48, 0.20),
        "4": (0.21, 0.56, 0.25),
        "5": (0.24, 0.64, 0.30),
    }.items():
        values = everbright["rank_values"][rank]
        assert values["all_attribute_damage_bonus"] == expected[0]
        assert values["resonance_liberation_def_ignore"] == expected[1]
        assert values["resonance_liberation_fusion_res_ignore"] == expected[2]

    profiles = load_build_profiles(DATA_DIR)
    profile = profiles["profiles"]["aemeath"]["aemeath_user_real_01"]
    before_components = json.dumps(profile["stat_components"], sort_keys=True)
    before_combat = json.dumps(profile["combat_stats"], sort_keys=True)
    before_bonuses = json.dumps(profile["damage_bonuses"], sort_keys=True)
    weapon = profile["weapon"]
    assert weapon["weapon_id"] == "everbright_polestar"
    assert weapon["rank"] == 1
    assert weapon["static_stats_already_in_profile"] is True
    assert weapon["base_atk_and_crit_already_in_profile"] is True

    characters = json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8-sig"))
    base = CharacterData.model_validate(next(item for item in characters if item["id"] == "aemeath"))
    effective = resolve_character_build_stats(base, "aemeath_user_real_01", profiles)
    profiles_without_weapon = copy.deepcopy(profiles)
    profiles_without_weapon["profiles"]["aemeath"]["aemeath_user_real_01"].pop("weapon", None)
    effective_without_weapon = resolve_character_build_stats(base, "aemeath_user_real_01", profiles_without_weapon)
    assert effective.weapon["weapon_id"] == "everbright_polestar"
    assert effective.effective_attack == effective_without_weapon.effective_attack
    assert effective.crit_rate == effective_without_weapon.crit_rate
    assert effective.crit_damage == effective_without_weapon.crit_damage
    assert json.dumps(profile["stat_components"], sort_keys=True) == before_components
    assert json.dumps(profile["combat_stats"], sort_keys=True) == before_combat
    assert json.dumps(profile["damage_bonuses"], sort_keys=True) == before_bonuses

    damage_formula = (ROOT / "simulator" / "damage_formula.py").read_text(encoding="utf-8")
    assert "everbright_polestar" not in damage_formula
    assert "Everbright" not in damage_formula
    ast.parse(damage_formula)
    weapon_effects_source = (ROOT / "simulator" / "weapon_effects.py").read_text(encoding="utf-8")
    assert "conditional_penetration_buff" in weapon_effects_source
    assert "weapon_runtime_damage_effects" in weapon_effects_source

    print("everbright_polestar_loading_smoke_test ok")


if __name__ == "__main__":
    main()
