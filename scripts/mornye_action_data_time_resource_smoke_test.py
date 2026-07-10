from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from mornye_action_data_source_guard_smoke_test import OUTPUT as SOURCE_GUARD_OUTPUT
from mornye_action_data_source_guard_smoke_test import main as run_source_guard
from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-4) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def mornye_state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["mornye"]


def set_concerto(sim: Simulation, character_id: str, amount: float) -> None:
    state = sim.state.character_states[character_id]
    ensure_concerto_state(state)
    state["concerto_energy"] = min(amount, state["concerto_energy_cap"])
    state["concerto_ready"] = state["concerto_energy"] >= state["concerto_energy_cap"]
    sim.state.concerto_energy[character_id] = state["concerto_energy"]


def setup_intro_transition() -> Simulation:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_test_party")
    assert sim.state.active_character_id == "mornye"
    assert sim.execute_action("swap_to_aemeath")
    sim.transition_config["characters"]["mornye"]["intro_qte"]["mode"] = "enabled"
    set_concerto(sim, "aemeath", 100.0)
    return sim


def load_source_guard() -> dict:
    run_source_guard()
    assert SOURCE_GUARD_OUTPUT.exists()
    return json.loads(SOURCE_GUARD_OUTPUT.read_text(encoding="utf-8"))


def test_source_guard_dependency() -> None:
    payload = load_source_guard()
    assert payload["interpretation"]["liberation"]["combat_time_cost"] == 0.0
    assert payload["interpretation"]["liberation"]["action_time"] == 282 / 60
    assert payload["interpretation"]["liberation"]["wide_field_observation_action_time"] == 296 / 60
    assert payload["interpretation"]["distributed_array"]["relative_momentum_gain_total"] == 60
    assert payload["interpretation"]["qte_intro"]["passive_concerto_source_confirmed"] is True


def test_liberation_combat_time() -> None:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    before_concerto = mornye_state(sim)["concerto_energy"]
    assert sim.execute_action("mornye_resonance_liberation")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "mornye_liberation_critical_protocol"
    assert_close(row.action_time, 282 / 60, "Liberation action_time")
    assert row.combat_time_cost == 0.0
    assert row.effective_combat_time_cost == 0.0
    assert row.has_global_time_stop is True
    assert row.global_time_stop_frames == 300.0
    assert row.combat_time_cost_source == "大招-全局时停 covers damage end frame"
    assert row.source_rows == [4150, 4151, 4153, 4154]
    assert row.concerto_gain == 20.0
    assert mornye_state(sim)["concerto_energy"] == before_concerto + 20.0
    assert row.mornye_liberation_crit_rate_bonus is not None
    assert row.mornye_liberation_crit_rate_bonus > 0.0


def test_inversion_combat_time() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_enabled_test_party")
    state = mornye_state(sim)
    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 30.0
    state["relative_momentum"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.resolved_action_id == "mornye_heavy_inversion"
    assert_close(row.action_time, 86 / 60, "Inversion action_time")
    assert_close(row.combat_time_cost, 86 / 60, "Inversion combat_time_cost")
    assert row.has_global_time_stop is False
    assert row.source_rows == [4135, 4136]
    assert row.source_status == "not_source_confirmed_direct_interfered"
    assert state["relative_momentum"] == 0.0
    assert state["observation_marker_active"] is True
    assert row.mornye_interfered_marker_mode == "tune_break_triggered"
    assert row.mornye_interfered_marker_applied is False


def test_qte_intro_resources() -> None:
    sim = setup_intro_transition()
    mornye_state(sim)["rest_mass_energy"] = 80.0
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.resolved_action_id == "transition:mornye_intro_convergence"
    assert_close(row.action_time, 110 / 60, "QTE action_time")
    assert_close(row.combat_time_cost, 110 / 60, "QTE combat_time_cost")
    assert row.has_global_time_stop is False
    assert row.source_rows == [4148, 4149, 4164]
    assert row.base_concerto_gain == 10.0
    assert row.passive_concerto_gain == 20.0
    assert row.final_concerto_gain == 30.0
    assert row.concerto_gain == 30.0
    assert state["mode"] == "wide_field_observation"
    assert state["rest_mass_energy"] == 0.0
    assert_close(state["wide_field_observation_remaining"], 30.0, "QTE WFO remaining")
    assert "mornye_intro_convergence" not in sim.get_policy_action_ids()
    assert "transition:mornye_intro_convergence" not in sim.get_policy_action_ids()


def test_distributed_array_resource_gain() -> None:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    state = mornye_state(sim)
    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 30.0
    state["relative_momentum"] = 20.0
    before_concerto = state["concerto_energy"]
    assert sim.execute_action("mornye_resonance_skill")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.resolved_action_id == "mornye_skill_distributed_array"
    assert row.concerto_gain == 10.0
    assert state["concerto_energy"] == before_concerto + 10.0
    assert state["relative_momentum"] == 80.0
    assert row.relative_momentum_gain == 60.0
    assert row.relative_momentum_gain_source_rows == [4144, 4145, 4146, 4147]
    assert row.distributed_array_relative_momentum_gain_per_hit == [15.0, 15.0, 15.0, 15.0]

    state["relative_momentum"] = 70.0
    assert sim.execute_action("short_wait")
    sim.state.cooldowns["mornye_distributed_array"] = 0.0
    assert sim.execute_action("mornye_resonance_skill")
    assert mornye_state(sim)["relative_momentum"] == 100.0


def test_observation_a3_passive() -> None:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    state = mornye_state(sim)
    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 30.0
    state["wfo_combo_stage"] = 3
    before_concerto = state["concerto_energy"]
    assert sim.execute_action("mornye_basic_attack")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.resolved_action_id == "mornye_wfo_basic_stage_3"
    assert state["relative_momentum"] == 18.0
    assert state["concerto_energy"] == before_concerto + 22.56
    assert row.concerto_gain == 22.56
    assert row.passive_concerto_gain == 20.0
    assert row.final_concerto_gain == 20.0
    assert row.passive_concerto_source


def test_no_unintended_policy_exposure() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_test_party")
    policy_ids = sim.get_policy_action_ids()
    assert "mornye_intro_convergence" not in policy_ids
    assert "transition:mornye_intro_convergence" not in policy_ids
    assert "mornye_skill_optimal_solution" not in policy_ids
    assert "mornye_skill_distributed_array" not in policy_ids


def main() -> None:
    test_source_guard_dependency()
    test_liberation_combat_time()
    test_inversion_combat_time()
    test_qte_intro_resources()
    test_distributed_array_resource_gain()
    test_observation_a3_passive()
    test_no_unintended_policy_exposure()
    print("mornye_action_data_time_resource_smoke_test ok")


if __name__ == "__main__":
    main()
