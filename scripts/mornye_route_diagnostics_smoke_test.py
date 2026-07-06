from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config, transition_event_counts


def config_with_expectation_error_mode(mode: str) -> dict[str, Any]:
    config = deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("mornye", {})["mornye_expectation_error_mode"] = mode
    return config


def set_concerto(sim: Simulation, character_id: str, amount: float) -> None:
    state = sim.state.character_states[character_id]
    ensure_concerto_state(state)
    state["concerto_energy"] = min(amount, state["concerto_energy_cap"])
    state["concerto_ready"] = state["concerto_energy"] >= state["concerto_energy_cap"]
    sim.state.concerto_energy[character_id] = state["concerto_energy"]


def summarize(name: str, sim: Simulation) -> dict[str, Any]:
    summary = sim.summary()
    mornye_state = sim.state.character_states.get("mornye", {})
    milestone_rows = [
        row for row in sim.timeline
        if row.resolved_action_id in {
            "mornye_liberation_critical_protocol",
            "mornye_skill_expectation_error",
            "mornye_skill_optimal_solution",
            "mornye_heavy_geopotential_shift",
            "mornye_heavy_inversion",
            "mornye_skill_distributed_array",
            "mornye_tune_break",
            "transition:mornye_intro_convergence",
            "swap_to_aemeath",
        }
        or row.outgoing_outro_applied
        or row.incoming_intro_applied
    ]
    return {
        "route": name,
        "total_damage": summary.total_damage,
        "combat_time": summary.final_time,
        "time_to_wfo": next(
            (row.combat_time_end for row in sim.timeline if row.mornye_mode_after == "wide_field_observation"),
            None,
        ),
        "time_to_inversion": next(
            (row.combat_time_end for row in sim.timeline if row.resolved_action_id == "mornye_heavy_inversion"),
            None,
        ),
        "time_to_interfered_marker": next(
            (row.combat_time_end for row in sim.timeline if row.mornye_interfered_marker_applied),
            None,
        ),
        "time_to_concerto_ready": next(
            (
                row.combat_time_end
                for row in sim.timeline
                if row.actor_character_id == "mornye"
                and row.final_concerto_gain > 0
                and row.concerto_after >= 100.0
            ),
            None,
        ),
        "time_to_outro": next(
            (row.combat_time_end for row in sim.timeline if row.outgoing_outro_applied),
            None,
        ),
        "mornye_resources": {
            "rest_mass_energy": mornye_state.get("rest_mass_energy"),
            "relative_momentum": mornye_state.get("relative_momentum"),
            "wide_field_observation_remaining": mornye_state.get("wide_field_observation_remaining"),
            "concerto_energy": mornye_state.get("concerto_energy"),
        },
        "optimal_solution_triggered": any(row.optimal_solution_triggered for row in sim.timeline),
        "interfered_marker_triggered": any(row.mornye_interfered_marker_applied for row in sim.timeline),
        "outro_triggered": any(row.outgoing_outro_applied for row in sim.timeline),
        "transition_event_counts": transition_event_counts(summary.timeline),
        "resolved_actions": [row.resolved_action_id for row in sim.timeline],
        "milestones": [
            {
                "selected": row.selected_action_id,
                "resolved": row.resolved_action_id,
                "combat_time_end": row.combat_time_end,
                "combat_time_cost": row.combat_time_cost,
                "has_global_time_stop": row.has_global_time_stop,
                "source_rows": row.source_rows,
                "concerto_gain": row.concerto_gain,
                "base_concerto_gain": row.base_concerto_gain,
                "passive_concerto_gain": row.passive_concerto_gain,
                "relative_momentum_gain": row.relative_momentum_gain,
                "outro": row.outgoing_outro_applied,
            }
            for row in milestone_rows
        ],
    }


def run_liberation_skill_swap(mode: str) -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        transition_config=config_with_expectation_error_mode(mode),
    )
    sim.execute_action("mornye_resonance_liberation")
    sim.execute_action("mornye_resonance_skill")
    sim.execute_action("swap_to_aemeath")
    return sim


def run_conservative_wfo_inversion_route() -> Simulation:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_enabled_test_party")
    state = sim.state.character_states["mornye"]
    state["rest_mass_energy"] = 100.0
    sim.execute_action("mornye_heavy_attack")
    state["relative_momentum"] = 100.0
    sim.execute_action("mornye_heavy_attack")
    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 25.0
    sim.execute_action("mornye_tune_break")
    return sim


def run_intro_outro_resource_route() -> Simulation:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_enabled_test_party")
    sim.execute_action("swap_to_aemeath")
    set_concerto(sim, "aemeath", 100.0)
    sim.execute_action("swap_to_mornye")
    set_concerto(sim, "mornye", 100.0)
    sim.execute_action("swap_to_aemeath")
    return sim


def main() -> None:
    diagnostics = [
        summarize("conservative_liberation_skill_swap", run_liberation_skill_swap("expectation_error_only")),
        summarize("always_success_liberation_skill_swap", run_liberation_skill_swap("always_success")),
        summarize("conservative_wfo_inversion", run_conservative_wfo_inversion_route()),
        summarize("enabled_intro_outro_resource_route", run_intro_outro_resource_route()),
    ]
    assert diagnostics[0]["optimal_solution_triggered"] is False
    assert diagnostics[1]["optimal_solution_triggered"] is True
    assert diagnostics[2]["interfered_marker_triggered"] is True
    intro_milestones = diagnostics[3]["milestones"]
    intro_row = next(row for row in intro_milestones if row["resolved"] == "transition:mornye_intro_convergence")
    outro_row = next(row for row in intro_milestones if row["outro"])
    assert intro_row["concerto_gain"] == 30.0
    assert intro_row["base_concerto_gain"] == 10.0
    assert intro_row["passive_concerto_gain"] == 20.0
    assert intro_row["has_global_time_stop"] is False
    assert outro_row["outro"] is True
    print(json.dumps(diagnostics, indent=2))
    print("Mornye route diagnostics smoke test passed.")


if __name__ == "__main__":
    main()
