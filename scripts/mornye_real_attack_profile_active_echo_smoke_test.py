from __future__ import annotations

import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
EXPECTED_ATK = 1159.1645


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    profiles = json.loads((ROOT / "data" / "build_profiles.json").read_text(encoding="utf-8-sig"))
    profile = profiles["profiles"]["mornye"]["mornye_user_real_01"]
    atk = profile["stat_components"]["atk"]
    assert atk == {
        "character_base": 287.0,
        "weapon_base": 412.5,
        "percent": 0.071,
        "flat": 410.0,
        "final_reference": 1159.1645,
    }
    calculated = (atk["character_base"] + atk["weapon_base"]) * (1.0 + atk["percent"]) + atk["flat"]
    assert_close(calculated, EXPECTED_ATK, "stored ATK component formula")
    assert profile["required_scaling_stats"] == ["def", "atk"]
    assert profile["default_scaling_stat"] == "def"
    assert_close(profile["stat_components"]["def"]["final_reference"], 2997.0536, "Mornye DEF")
    assert_close(profile["combat_stats"]["energy_regen"], 2.5424, "Mornye Energy Regen")

    sim = Simulation.from_json("data", selected_character_ids=PARTY_ID, initial_active_character="mornye")
    validation = sim.build_profile_validation
    assert validation["ok"] is True
    assert validation["errors"] == []
    assert not any("stat_components.atk." in item for item in validation.get("errors", []))
    assert not any("stat_components.atk." in item for item in validation.get("warnings", []))

    character = sim.characters["mornye"]
    assert character.profile_completeness_status == "user_supplied_complete"
    assert_close(character.static_atk, EXPECTED_ATK, "effective profile static ATK")
    assert_close(character.effective_atk, EXPECTED_ATK, "effective profile ATK")
    assert_close(character.final_atk_reference, EXPECTED_ATK, "effective profile ATK reference")
    assert_close(character.atk_reference_delta or 0.0, 0.0, "ATK reference delta")

    sim.state.resonance_energy["mornye"] = 0.0
    assert sim.execute_action("mornye_echo_reactor_husk")
    row = sim.timeline[-1]
    hit = row.hit_details[0]
    assert row.profile_completeness_status == "user_supplied_complete"
    assert hit["scaling_stat"] == "atk"
    assert_close(hit["scaling_value"], EXPECTED_ATK, "hit scaling value")
    assert_close(hit["static_atk"], EXPECTED_ATK, "hit static ATK")
    assert_close(hit["effective_atk"], EXPECTED_ATK, "hit effective ATK")
    assert_close(hit["final_atk_reference"], EXPECTED_ATK, "hit ATK reference")
    assert_close(hit["atk_reference_delta"] or 0.0, 0.0, "hit ATK reference delta")
    assert row.damage > 0.0
    assert_close(row.damage, 2071.3932654700507, "Reactor Husk damage", tolerance=1e-6)
    assert row.damage_bonus_category == "echo_ability"
    assert_close(row.base_resonance_energy_gain, 4.87, "base RE")
    assert_close(row.final_resonance_energy_gain, 12.381488, "final RE")
    assert_close(sim.state.cooldowns["mornye_echo_reactor_husk"], 20.0, "cooldown")
    print("mornye_real_attack_profile_active_echo_smoke_test ok")


if __name__ == "__main__":
    main()
