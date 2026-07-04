from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env.action_mask import action_mask
from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def mask_for(sim: Simulation) -> dict[str, bool]:
    return dict(zip(sim.get_policy_action_ids(), [bool(item) for item in action_mask(sim)]))


def set_full_concerto(sim: Simulation, character_id: str) -> None:
    state = sim.state.character_states[character_id]
    ensure_concerto_state(state)
    state["concerto_energy"] = state["concerto_energy_cap"]
    state["concerto_ready"] = True
    sim.state.concerto_energy[character_id] = state["concerto_energy"]


def main() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_test_party")
    assert sim.selected_party_character_ids == ["mornye", "aemeath", "dummy_sub_dps"]
    assert sim.state.active_character_id == "mornye"
    policy_ids = sim.get_policy_action_ids()
    assert "mornye_basic_attack" in policy_ids
    assert "aemeath_basic_attack" in policy_ids
    assert "swap_to_aemeath" in policy_ids
    assert "swap_to_mornye" in policy_ids
    assert "mornye_outro_recursion" not in policy_ids
    assert "mornye_intro_convergence" not in policy_ids
    assert "mornye_skill_expectation_error" not in policy_ids
    assert "mornye_skill_optimal_solution" not in policy_ids
    assert "aemeath_qte_intro_human" not in policy_ids
    assert "aemeath_qte_intro_mech" not in policy_ids
    assert sim.transition_config["mechanics"]["mornye"]["mornye_expectation_error_mode"] == "expectation_error_only"

    start_mask = mask_for(sim)
    assert start_mask["mornye_basic_attack"] is True
    assert start_mask["mornye_resonance_skill"] is True
    assert start_mask["aemeath_basic_attack"] is False
    assert start_mask["swap_to_mornye"] is False
    assert start_mask["swap_to_aemeath"] is True

    set_full_concerto(sim, "mornye")
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.outgoing_outro_event_id == "mornye_outro_recursion"
    assert row.outgoing_outro_applied is True
    assert row.incoming_qte_mode == "disabled"
    assert row.incoming_qte_applied is False
    assert row.incoming_qte_candidate_id in {"aemeath_qte_intro_human", "aemeath_qte_intro_mech"}
    assert "mornye_outro_recursion_all_dmg_amp" in row.applied_buffs

    swapped_mask = mask_for(sim)
    assert swapped_mask["mornye_basic_attack"] is False
    assert swapped_mask["aemeath_basic_attack"] is True
    assert swapped_mask["swap_to_mornye"] is True
    assert swapped_mask["swap_to_aemeath"] is False

    assert sim.execute_action("swap_to_mornye")
    assert sim.state.active_character_id == "mornye"
    back_mask = mask_for(sim)
    assert back_mask["mornye_basic_attack"] is True
    assert back_mask["aemeath_basic_attack"] is False

    print("Mornye party integration smoke test passed.")


if __name__ == "__main__":
    main()
