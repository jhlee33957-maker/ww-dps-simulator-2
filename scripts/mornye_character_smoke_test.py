from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from characters.mornye import MornyeMechanic
from characters.registry import get_mechanic
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def mornye_state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["mornye"]


def test_initial_state_and_policy_actions() -> None:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    state = mornye_state(sim)
    assert isinstance(get_mechanic("mornye"), MornyeMechanic)
    assert state["mode"] == "baseline"
    assert state["rest_mass_energy"] == 0.0
    assert state["rest_mass_energy_cap"] == 100.0
    assert state["relative_momentum"] == 0.0
    assert state["relative_momentum_cap"] == 100.0
    assert state["concerto_energy"] == 0.0
    assert state["concerto_energy_cap"] == 100.0

    policy_ids = sim.get_policy_action_ids()
    for action_id in (
        "mornye_basic_attack",
        "mornye_heavy_attack",
        "mornye_resonance_skill",
        "mornye_resonance_liberation",
    ):
        assert action_id in policy_ids
    assert "mornye_outro_recursion" not in policy_ids
    assert "mornye_intro_convergence" not in policy_ids
    assert "mornye_skill_expectation_error" not in policy_ids
    assert "mornye_skill_optimal_solution" not in policy_ids


def test_resonance_skill_defaults_to_expectation_error() -> None:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    assert sim.execute_action("mornye_resonance_skill")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.selected_action_id == "mornye_resonance_skill"
    assert row.resolved_action_id == "mornye_skill_expectation_error"
    assert row.optimal_solution_triggered is False
    assert row.optimal_solution_trigger_reason == "gp_success_not_modeled"
    assert row.total_action_damage == 0.0
    assert state["rest_mass_energy"] == 0.0


def test_basic_resolves_and_builds_rest_mass() -> None:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    assert sim.execute_action("mornye_basic_attack")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.selected_action_id == "mornye_basic_attack"
    assert row.resolved_action_id == "mornye_basic_stage_1"
    assert row.total_action_damage > 0.0
    assert row.hit_count == 3
    assert state["baseline_combo_stage"] == 2
    assert state["rest_mass_energy"] == 20.0


def test_heavy_geopotential_shift_enters_wfo() -> None:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    state = mornye_state(sim)
    state["rest_mass_energy"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.resolved_action_id == "mornye_heavy_geopotential_shift"
    assert state["rest_mass_energy"] == 0.0
    assert state["mode"] == "wide_field_observation"
    assert state["wide_field_observation_remaining"] == 30.0
    assert state["syntony_field_remaining"] == 25.0


def test_wfo_basic_and_liberation_high_syntony() -> None:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    state = mornye_state(sim)
    state["rest_mass_energy"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    assert sim.execute_action("mornye_basic_attack")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.resolved_action_id == "mornye_wfo_basic_stage_1"
    assert state["relative_momentum"] > 0.0
    assert state["wfo_combo_stage"] == 2

    assert sim.execute_action("mornye_resonance_liberation")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.resolved_action_id == "mornye_liberation_critical_protocol"
    assert state["syntony_field_remaining"] == 0.0
    assert 0.0 < state["high_syntony_field_remaining"] < 25.0
    assert row.high_syntony_field_same_action_application is True
    assert row.high_syntony_field_def_bonus_active is True


def test_wfo_inversion_requires_relative_momentum() -> None:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    state = mornye_state(sim)
    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 30.0
    state["relative_momentum"] = 99.0
    assert sim.is_action_available(sim.actions["mornye_heavy_attack"]) is False
    state["relative_momentum"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.resolved_action_id == "mornye_heavy_inversion"
    assert state["relative_momentum"] == 0.0
    assert state["observation_marker_active"] is True
    assert state["observation_marker_remaining"] == 30.0


def main() -> None:
    test_initial_state_and_policy_actions()
    test_resonance_skill_defaults_to_expectation_error()
    test_basic_resolves_and_builds_rest_mass()
    test_heavy_geopotential_shift_enters_wfo()
    test_wfo_basic_and_liberation_high_syntony()
    test_wfo_inversion_requires_relative_momentum()
    print("Mornye character smoke test passed.")


if __name__ == "__main__":
    main()
