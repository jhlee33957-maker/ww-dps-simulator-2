from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.tune_break import calculate_tune_break_damage_detail
from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-3) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def main() -> None:
    detail = calculate_tune_break_damage_detail(
        tune_break_multiplier=16.0,
        additional_tune_break_boost=0.4,
        tune_dmg_bonus=0.0,
        enemy_res=0.2,
        res_pen=0.0,
        attacker_level=90,
        enemy_level=90,
        def_reduction=0.0,
    )
    assert detail["tune_break_base_value"] == 10000.0
    assert_close(detail["tune_break_res_multiplier"], 0.8, "RES")
    assert_close(detail["tune_break_def_multiplier"], 0.5013003901170351, "DEF")
    assert_close(detail["tune_break_damage"], 89833.0, "Tune Break damage", tol=10.0)

    low = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    high = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    for sim in (low, high):
        sim.state.enemy_tune_break_available = True
        sim.state.enemy_mistune_active = True
    high.characters["mornye"].static_def = 999999.0
    high.characters["mornye"].static_atk = 999999.0
    high.characters["mornye"].static_hp = 999999.0
    assert low.execute_action("mornye_tune_break")
    assert high.execute_action("mornye_tune_break")
    assert_close(low.timeline[-1].tune_break_damage, high.timeline[-1].tune_break_damage, "stat independence")
    assert low.timeline[-1].effective_damage_bonus == 0.0

    print("tune_break_formula_smoke_test ok")


if __name__ == "__main__":
    main()
