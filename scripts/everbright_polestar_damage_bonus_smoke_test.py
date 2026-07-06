from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation
from simulator.tune_break import calculate_tune_response_damage_detail


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def make_sim(rank: int = 1, *, remove_weapon: bool = False) -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
    )
    if remove_weapon:
        sim.characters["aemeath"].weapon = {}
    else:
        sim.characters["aemeath"].weapon["rank"] = rank
    return sim


def main() -> None:
    sim = make_sim(rank=1)
    assert sim.weapon_definitions["weapons"]["everbright_polestar"]["rank_values"]["1"]["all_attribute_damage_bonus"] == 0.12
    assert sim.execute_action("aemeath_basic_form_stage_1")
    row = sim.timeline[-1]
    assert row.damage_element == "fusion"
    assert row.everbright_polestar_all_attribute_bonus_active is True
    assert_close(row.everbright_polestar_all_attribute_damage_bonus, 0.12, "R1 all attribute")
    assert_close(row.runtime_all_attribute_damage_bonus, 0.12, "runtime all attribute")
    assert_close(row.runtime_element_damage_bonus, 0.12, "runtime element bonus")
    assert_close(row.element_damage_bonus_before_weapon, 0.40, "element before weapon")
    assert_close(row.element_damage_bonus_after_weapon, 0.52, "element after weapon")

    baseline = make_sim(remove_weapon=True)
    assert baseline.execute_action("aemeath_basic_form_stage_1")
    assert row.total_action_damage > baseline.timeline[-1].total_action_damage

    tune = make_sim()
    tune.state.enemy_tune_break_available = True
    tune.state.enemy_mistune_active = True
    assert tune.execute_action("aemeath_tune_break")
    tune_row = tune.timeline[-1]
    assert tune_row.damage_bonus_category == "tune_break"
    assert_close(tune_row.everbright_polestar_all_attribute_damage_bonus, 0.0, "Tune Break all attribute exclusion")
    assert_close(tune_row.runtime_element_damage_bonus, 0.0, "Tune Break runtime element exclusion")

    response_detail = calculate_tune_response_damage_detail(
        tune_response_id="aemeath_starburst",
        tune_response_hit_id="aemeath_starburst_1",
        tune_response_multiplier=5.9643,
        enemy_res=0.1,
        res_pen=0.0,
        attacker_level=90,
        enemy_level=90,
        tune_response_element="fusion",
    )
    assert "everbright_polestar_all_attribute_damage_bonus" not in response_detail

    rank5 = make_sim(rank=5)
    assert rank5.execute_action("aemeath_basic_form_stage_1")
    rank5_row = rank5.timeline[-1]
    assert_close(rank5_row.everbright_polestar_all_attribute_damage_bonus, 0.24, "R5 all attribute")
    assert_close(rank5_row.runtime_element_damage_bonus, 0.24, "R5 runtime element")

    copied_profile = copy.deepcopy(sim.characters["aemeath"].damage_bonuses)
    assert copied_profile["by_element"]["fusion"] == 0.4
    assert sim.characters["aemeath"].damage_bonuses == copied_profile

    print("everbright_polestar_damage_bonus_smoke_test ok")


if __name__ == "__main__":
    main()
