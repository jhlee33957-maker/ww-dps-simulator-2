from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation
from simulator.resource_system import ensure_concerto_state


DATA_DIR = PROJECT_ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def set_full_concerto(sim: Simulation, character_id: str) -> None:
    state = sim.state.character_states[character_id]
    ensure_concerto_state(state)
    state["concerto_energy"] = state["concerto_energy_cap"]
    state["concerto_ready"] = True
    sim.state.concerto_energy[character_id] = state["concerto_energy"]


def main() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    policy_actions = sim.get_policy_action_ids()
    assert "swap_to_dummy_support" in policy_actions
    assert "swap_to_dummy_sub_dps" in policy_actions
    assert "swap_to_aemeath" in policy_actions
    assert not sim.is_action_available(sim.actions["swap_to_aemeath"])
    assert sim.is_action_available(sim.actions["swap_to_dummy_support"])

    assert sim.execute_action("swap_to_dummy_support")
    row = sim.timeline[-1]
    assert sim.state.active_character_id == "dummy_support"
    assert_close(sim.state.combat_time, 0.5, "swap combat_time")
    assert_close(row.action_time, 0.5, "swap action_time")
    assert_close(row.combat_time_cost, 0.5, "swap full combat cost")
    assert_close(row.effective_combat_time_cost, 0.5, "swap effective combat cost")
    assert row.actor_character_id == "aemeath"
    assert row.active_character_before == "aemeath"
    assert row.active_character_after == "dummy_support"
    assert row.outgoing_character_id == "aemeath"
    assert row.incoming_character_id == "dummy_support"
    assert row.transition_type == "normal_swap"
    assert row.transition_reason == "concerto_not_ready"
    assert row.fallback_swap_used is True
    assert row.swap_timing_is_placeholder is True
    assert row.swap_timing_source == "party_presets.aemeath_test_party.generic_swap"
    assert row.transition_events == []

    assert not sim.is_action_available(sim.actions["swap_to_dummy_support"])
    assert sim.is_action_available(sim.actions["dummy_support_attack"])
    assert sim.is_action_available(sim.actions["dummy_support_buff"])
    assert not sim.is_action_available(sim.actions["aemeath_basic_attack"])
    assert sim.is_action_available(sim.actions["swap_to_aemeath"])

    set_full_concerto(sim, "dummy_support")
    assert sim.execute_action("swap_to_aemeath")
    outro_row = sim.timeline[-1]
    assert_close(outro_row.action_time, 0.5, "outro fallback swap action_time")
    assert outro_row.outgoing_character_id == "dummy_support"
    assert outro_row.incoming_character_id == "aemeath"
    assert outro_row.transition_type == "full_concerto_transition"
    assert outro_row.transition_reason == "concerto_ready_qte_disabled"
    assert outro_row.outgoing_outro_event_id == "dummy_support_outro_damage_amp"
    assert outro_row.outgoing_outro_applied is True
    assert outro_row.incoming_qte_mode == "disabled"
    assert outro_row.incoming_qte_applied is False
    assert outro_row.fallback_swap_used is True
    assert outro_row.swap_timing_is_placeholder is True
    assert "dummy_support_outro_damage_amp" in outro_row.applied_buffs

    mornye_sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_test_party")
    assert mornye_sim.state.active_character_id == "mornye"
    set_full_concerto(mornye_sim, "mornye")
    assert mornye_sim.execute_action("swap_to_aemeath")
    mornye_outro_row = mornye_sim.timeline[-1]
    assert mornye_outro_row.outgoing_character_id == "mornye"
    assert mornye_outro_row.incoming_character_id == "aemeath"
    assert mornye_outro_row.outgoing_outro_event_id == "mornye_outro_recursion"
    assert mornye_outro_row.outgoing_outro_applied is True
    assert mornye_outro_row.outgoing_concerto_consumed is True
    assert "mornye_outro_recursion_all_dmg_amp" in mornye_outro_row.applied_buffs

    print("Party swap smoke test passed.")


if __name__ == "__main__":
    main()
