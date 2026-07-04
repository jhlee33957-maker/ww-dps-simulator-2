from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from characters.mornye import (
    get_energy_regen,
    get_energy_regen_excess_percent,
    get_interfered_damage_amp,
    get_liberation_crit_bonuses,
)
from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, message: str, tolerance: float = 1e-6) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def make_mornye_sim(energy_regen: float) -> Simulation:
    sim = Simulation.from_json(DATA_DIR, party="mornye")
    sim.characters["mornye"].energy_regen = energy_regen
    sim.state.character_states["mornye"]["energy_regen"] = energy_regen
    sim.state.resonance_energy["mornye"] = sim.characters["mornye"].resonance_energy_max
    return sim


def test_mornye_er_helper_formulas() -> None:
    state = {"energy_regen": 2.6}
    assert_close(get_energy_regen(state), 2.6, "ER helper")
    assert_close(get_energy_regen_excess_percent(state), 160.0, "ER excess percent")
    assert_close(get_interfered_damage_amp({"energy_regen": 1.0}), 0.0, "100% ER marker amp")
    assert_close(get_interfered_damage_amp({"energy_regen": 1.6}), 0.15, "160% ER marker amp")
    assert_close(get_interfered_damage_amp(state), 0.40, "260% ER marker amp cap")
    crit_rate_bonus, crit_dmg_bonus = get_liberation_crit_bonuses(state)
    assert_close(crit_rate_bonus, 0.80, "260% ER Liberation CR cap")
    assert_close(crit_dmg_bonus, 1.60, "260% ER Liberation CD cap")


def test_liberation_only_receives_er_crit_scaling() -> None:
    basic_low_er = make_mornye_sim(1.0)
    basic_high_er = make_mornye_sim(2.6)
    assert basic_low_er.execute_action("mornye_basic_attack"), "Low ER basic should execute"
    assert basic_high_er.execute_action("mornye_basic_attack"), "High ER basic should execute"
    assert_close(
        basic_high_er.timeline[-1].normal_damage,
        basic_low_er.timeline[-1].normal_damage,
        "Mornye basic damage should not directly scale with ER",
    )

    liberation_low_er = make_mornye_sim(1.0)
    liberation_high_er = make_mornye_sim(2.6)
    assert liberation_low_er.execute_action("mornye_resonance_liberation"), "Low ER liberation should execute"
    assert liberation_high_er.execute_action("mornye_resonance_liberation"), "High ER liberation should execute"
    low_row = liberation_low_er.timeline[-1]
    high_row = liberation_high_er.timeline[-1]

    assert high_row.normal_damage > low_row.normal_damage, "High ER Liberation should gain temporary crit damage"
    assert_close(high_row.mornye_er_excess_percent or 0.0, 160.0, "Liberation ER excess log")
    assert_close(high_row.mornye_liberation_crit_rate_bonus or 0.0, 0.80, "Liberation CR log")
    assert_close(high_row.mornye_liberation_crit_dmg_bonus or 0.0, 1.60, "Liberation CD log")
    assert low_row.mornye_liberation_crit_rate_bonus == 0.0, "100% ER should log zero CR bonus"
    assert low_row.mornye_liberation_crit_dmg_bonus == 0.0, "100% ER should log zero CD bonus"


def test_energy_regen_patch_does_not_force_optimal_solution() -> None:
    sim = make_mornye_sim(2.6)
    assert sim.execute_action("mornye_resonance_skill"), "Mornye skill should execute"
    row = sim.timeline[-1]
    assert row.resolved_action_id == "mornye_skill_expectation_error"
    assert row.optimal_solution_triggered is False


if __name__ == "__main__":
    test_mornye_er_helper_formulas()
    test_liberation_only_receives_er_crit_scaling()
    test_energy_regen_patch_does_not_force_optimal_solution()
    print("mornye_energy_regen_scaling_smoke_test ok")
