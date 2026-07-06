from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.damage_formula import calc_def_multiplier, calc_res_multiplier
from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def config() -> dict:
    value = copy.deepcopy(load_transition_config(DATA_DIR))
    value.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = "fusion_burst"
    return value


def make_sim() -> Simulation:
    return Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
        transition_config=config(),
    )


def main() -> None:
    with_penetration = make_sim()
    no_penetration = make_sim()
    assert with_penetration.execute_action("aemeath_basic_form_stage_3")
    assert with_penetration.execute_action("aemeath_heavy_aemeath_charged_1")
    assert no_penetration.execute_action("aemeath_heavy_aemeath_charged_1")

    row = with_penetration.timeline[-1]
    baseline = no_penetration.timeline[-1]
    assert row.total_action_damage > baseline.total_action_damage
    assert_close(row.def_ignore_before_weapon, 0.03, "DEF Ignore before weapon")
    assert_close(row.everbright_polestar_def_ignore_bonus, 0.32, "DEF Ignore weapon bonus")
    assert_close(row.total_def_ignore, 0.35, "total DEF Ignore")
    assert_close(
        row.def_multiplier_before_weapon,
        calc_def_multiplier(90, 90, 0.03, 0.0),
        "DEF multiplier before",
    )
    assert_close(
        row.def_multiplier_after_weapon,
        calc_def_multiplier(90, 90, 0.35, 0.0),
        "DEF multiplier after",
    )
    assert row.def_multiplier_after_weapon > row.def_multiplier_before_weapon

    assert_close(row.enemy_res_before_weapon, 0.10, "enemy RES before")
    assert_close(row.everbright_polestar_fusion_res_ignore_bonus, 0.10, "Fusion RES Ignore weapon bonus")
    assert_close(row.enemy_res_after_weapon, 0.0, "enemy RES after")
    assert_close(row.res_multiplier_before_weapon, calc_res_multiplier(0.10), "RES multiplier before")
    assert_close(row.res_multiplier_after_weapon, calc_res_multiplier(0.0), "RES multiplier after")
    assert row.res_multiplier_after_weapon > row.res_multiplier_before_weapon
    assert row.everbright_polestar_def_ignore_bonus not in {
        row.all_dmg_bonus,
        row.category_dmg_bonus,
        row.element_dmg_bonus,
        row.effective_damage_bonus,
    }

    detail = row.hit_details[0]
    for key in (
        "def_ignore_before_weapon",
        "everbright_polestar_def_ignore_bonus",
        "total_def_ignore",
        "enemy_res_before_weapon",
        "everbright_polestar_fusion_res_ignore_bonus",
        "enemy_res_after_weapon",
    ):
        assert key in detail
    assert detail["damage_element_fallback_used_for_weapon_res_ignore"] is True

    assert no_penetration.timeline[-1].everbright_polestar_def_ignore_bonus == 0.0
    assert no_penetration.timeline[-1].everbright_polestar_fusion_res_ignore_bonus == 0.0

    print("everbright_polestar_formula_integration_smoke_test ok")


if __name__ == "__main__":
    main()
