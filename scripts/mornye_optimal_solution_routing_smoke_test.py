from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


def config_with_expectation_error_mode(mode: str) -> dict:
    config = deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("mornye", {})["mornye_expectation_error_mode"] = mode
    return config


def run_skill(mode: str | None = None) -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="mornye",
        transition_config=config_with_expectation_error_mode(mode) if mode else None,
    )
    assert sim.execute_action("mornye_resonance_skill"), f"Mornye skill should execute in {mode or 'default'} mode"
    return sim


def test_default_conservative_mode() -> None:
    sim = run_skill()
    row = sim.timeline[-1]
    state = sim.state.character_states["mornye"]
    assert row.selected_action_id == "mornye_resonance_skill"
    assert row.resolved_action_id == "mornye_skill_expectation_error"
    assert row.mornye_expectation_error_mode == "expectation_error_only"
    assert row.base_policy_action_id == "mornye_resonance_skill"
    assert row.optimal_solution_triggered is False
    assert row.optimal_solution_trigger_reason == "gp_success_not_modeled"
    assert row.optimal_solution_candidate_id == "mornye_skill_optimal_solution"
    assert row.gp_success_modeled is False
    assert row.total_action_damage == 0.0
    assert state["rest_mass_energy"] == 0.0


def test_dry_run_candidate_mode() -> None:
    conservative = run_skill()
    dry_run = run_skill("dry_run_success_candidate")
    row = dry_run.timeline[-1]
    assert row.resolved_action_id == "mornye_skill_expectation_error"
    assert row.mornye_expectation_error_mode == "dry_run_success_candidate"
    assert row.optimal_solution_triggered is False
    assert row.optimal_solution_trigger_reason == "dry_run_success_candidate"
    assert row.optimal_solution_candidate_id == "mornye_skill_optimal_solution"
    assert row.total_action_damage == conservative.timeline[-1].total_action_damage
    assert dry_run.state.character_states["mornye"]["rest_mass_energy"] == conservative.state.character_states["mornye"]["rest_mass_energy"]


def test_always_success_mode_preserves_old_behavior_only_when_explicit() -> None:
    sim = run_skill("always_success")
    row = sim.timeline[-1]
    state = sim.state.character_states["mornye"]
    assert row.resolved_action_id == "mornye_skill_optimal_solution"
    assert row.mornye_expectation_error_mode == "always_success"
    assert row.optimal_solution_triggered is True
    assert row.optimal_solution_trigger_reason == "simplified_always_success"
    assert row.gp_success_modeled is True
    assert row.implementation_status == "simplified_always_success"
    assert row.total_action_damage > 0.0
    assert state["rest_mass_energy"] == 100.0


def test_wfo_skill_routes_to_distributed_array() -> None:
    sim = Simulation.from_json(DATA_DIR, party="mornye", transition_config=config_with_expectation_error_mode("always_success"))
    state = sim.state.character_states["mornye"]
    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 30.0
    assert sim.execute_action("mornye_resonance_skill")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "mornye_skill_distributed_array"
    assert row.optimal_solution_triggered is False
    assert row.optimal_solution_trigger_reason == "wide_field_observation_uses_distributed_array"
    assert row.optimal_solution_candidate_id is None


def test_policy_action_list_hides_internal_skill_actions() -> None:
    sim = Simulation.from_json(DATA_DIR, party="mornye")
    policy_ids = sim.get_policy_action_ids()
    assert "mornye_resonance_skill" in policy_ids
    assert "mornye_skill_optimal_solution" not in policy_ids
    assert "mornye_skill_expectation_error" not in policy_ids


def test_enabled_party_preset_remains_conservative() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_enabled_test_party")
    mode = sim.transition_config["mechanics"]["mornye"]["mornye_expectation_error_mode"]
    assert mode != "always_success"
    assert mode == "expectation_error_only"
    assert sim.transition_config["characters"]["aemeath"]["intro_qte"]["mode"] == "enabled"
    assert sim.transition_config["characters"]["mornye"]["intro_qte"]["mode"] == "enabled"
    assert sim.transition_config["characters"]["mornye"]["outro"]["enabled"] is True


if __name__ == "__main__":
    test_default_conservative_mode()
    test_dry_run_candidate_mode()
    test_always_success_mode_preserves_old_behavior_only_when_explicit()
    test_wfo_skill_routes_to_distributed_array()
    test_policy_action_list_hides_internal_skill_actions()
    test_enabled_party_preset_remains_conservative()
    print("Mornye Optimal Solution routing smoke test passed.")
