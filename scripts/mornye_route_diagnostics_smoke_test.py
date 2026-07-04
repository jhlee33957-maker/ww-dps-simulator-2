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

from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config, transition_event_counts


def config_with_expectation_error_mode(mode: str) -> dict[str, Any]:
    config = deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("mornye", {})["mornye_expectation_error_mode"] = mode
    return config


def summarize(name: str, sim: Simulation) -> dict[str, Any]:
    summary = sim.summary()
    mornye_state = sim.state.character_states.get("mornye", {})
    return {
        "route": name,
        "total_damage": summary.total_damage,
        "combat_time": summary.final_time,
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
    return sim


def main() -> None:
    diagnostics = [
        summarize("conservative_liberation_skill_swap", run_liberation_skill_swap("expectation_error_only")),
        summarize("always_success_liberation_skill_swap", run_liberation_skill_swap("always_success")),
        summarize("conservative_wfo_inversion", run_conservative_wfo_inversion_route()),
    ]
    assert diagnostics[0]["optimal_solution_triggered"] is False
    assert diagnostics[1]["optimal_solution_triggered"] is True
    assert diagnostics[2]["interfered_marker_triggered"] is True
    print(json.dumps(diagnostics, indent=2))
    print("Mornye route diagnostics smoke test passed.")


if __name__ == "__main__":
    main()
