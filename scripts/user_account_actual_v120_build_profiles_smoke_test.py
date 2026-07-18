from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.build_profiles import calculate_scaling_stat_components, load_build_profile_overlay, load_build_profiles
from simulator.weapon_effects import load_weapon_definition


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-9) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tol), f"{label}: {actual} != {expected}"


def static_value(profile: dict, stat: str) -> float:
    return calculate_scaling_stat_components(
        {stat: profile["stat_components"][stat]},
        profile.get("runtime_bonuses"),
    )[stat]["static_value"]


def main() -> None:
    profiles = load_build_profiles(DATA_DIR)["profiles"]
    overlay_profiles = load_build_profile_overlay(DATA_DIR)["profiles"]
    weapons = load_weapon_definition(DATA_DIR)["weapons"]

    aemeath = profiles["aemeath"]["aemeath_account_actual_01"]
    assert overlay_profiles["aemeath"]["aemeath_account_actual_01"]["simulation_ready"] is False
    assert aemeath["account_profile"] is True and aemeath["simulation_ready"] is True
    assert aemeath["constellation"]["mechanics_implemented"] is True
    assert aemeath["sequence"] == 6
    assert_close(static_value(aemeath, "atk"), 2657.584, "Aemeath calculated ATK")
    assert int(static_value(aemeath, "atk")) == 2657
    assert_close(aemeath["combat_stats"]["energy_regen"], 1.2, "Aemeath ER")
    assert_close(aemeath["damage_bonuses"]["by_element"]["fusion"], 0.4, "Aemeath static Fusion")
    assert aemeath["bonus_decomposition"]["fusion"]["do_not_store_future_total_in_static_profile"] is True
    assert_close(weapons["everbright_polestar"]["rank_values"]["1"]["all_attribute_damage_bonus"], 0.12, "Everbright runtime all")
    assert aemeath["damage_bonuses"]["by_element"]["fusion"] != 0.52

    lynae = profiles["lynae"]["lynae_account_actual_01"]
    assert overlay_profiles["lynae"]["lynae_account_actual_01"]["simulation_ready"] is False
    assert lynae["account_profile"] is True and lynae["simulation_ready"] is True
    assert lynae["constellation"]["mechanics_implemented"] is True
    assert lynae["sequence"] == 2
    assert_close(static_value(lynae, "atk"), 1929.758, "Lynae calculated ATK")
    assert int(static_value(lynae, "atk")) == 1929
    assert_close(lynae["combat_stats"]["energy_regen"], 1.548, "Lynae ER")
    assert_close(weapons["static_mist"]["rank_values"]["5"]["energy_regen_static_bonus"], 0.256, "Static Mist R5 ER metadata")
    assert_close(lynae["combat_stats"]["energy_regen"], 1.548, "Lynae ER remains final stat-screen value")
    assert not math.isclose(lynae["combat_stats"]["energy_regen"], 1.548 + 0.256, rel_tol=0.0, abs_tol=1e-9)

    mornye = profiles["mornye"]["mornye_account_actual_01"]
    assert overlay_profiles["mornye"]["mornye_account_actual_01"]["simulation_ready"] is False
    assert mornye["account_profile"] is True and mornye["simulation_ready"] is True
    assert mornye["constellation"]["mechanics_implemented"] is True
    assert mornye["sequence"] == 3
    assert_close(static_value(mornye, "atk"), 1158.629, "Mornye calculated ATK")
    assert int(static_value(mornye, "atk")) == 1158
    assert_close(static_value(mornye, "def"), 3357.1385, "Mornye calculated DEF")
    assert int(static_value(mornye, "def")) == 3357
    assert_close(mornye["combat_stats"]["energy_regen"], 2.7944, "Mornye ER")
    assert_close(weapons["starfield_calibrator"]["rank_values"]["5"]["def_percent_passive"], 0.32, "Starfield R5 DEF")
    assert_close(mornye["stat_components"]["def"]["percent"], 1.307, "Mornye stat-screen DEF percent")
    assert mornye["runtime_bonuses"]["def"]["percent"] == 0.0
    assert not math.isclose(mornye["stat_components"]["def"]["percent"], 1.307 + 0.32, rel_tol=0.0, abs_tol=1e-9)

    print("user_account_actual_v120_build_profiles_smoke_test ok")


if __name__ == "__main__":
    main()
