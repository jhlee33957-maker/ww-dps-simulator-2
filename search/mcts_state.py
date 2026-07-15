from __future__ import annotations

from pathlib import Path

from simulator.simulation import Simulation
from search.search_state_codec import execute_action_for_search, full_node_state_fingerprint, future_state_fingerprint


ROOT = Path(__file__).resolve().parents[1]


def create_initial_simulation(*, combat_duration: float = 120.0) -> Simulation:
    simulation = Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
        transition_config=None,
    )
    simulation.combat_duration = float(combat_duration)
    simulation.state.combat_duration = float(combat_duration)
    return simulation


def policy_action_ids(simulation: Simulation) -> tuple[str, ...]:
    actions = tuple(simulation.get_policy_action_ids())
    if len(actions) != 25 or len(set(actions)) != 25:
        raise AssertionError("MCTS requires the immutable ordered 25-action policy space")
    return actions


def legal_policy_slots(simulation: Simulation, actions: tuple[str, ...]) -> list[int]:
    available = set(simulation.valid_action_ids())
    return [slot for slot, action_id in enumerate(actions) if action_id in available]


def execute_policy_slot(simulation: Simulation, actions: tuple[str, ...], slot: int) -> bool:
    return execute_action_for_search(simulation, actions[int(slot)])


def node_metrics(simulation: Simulation) -> dict[str, float | str]:
    return {
        "total_damage": float(simulation.state.total_damage),
        "combat_time": float(simulation.state.combat_time),
        "current_time": float(simulation.state.current_time),
        "full_fingerprint": full_node_state_fingerprint(simulation),
        "future_fingerprint": future_state_fingerprint(simulation),
    }
