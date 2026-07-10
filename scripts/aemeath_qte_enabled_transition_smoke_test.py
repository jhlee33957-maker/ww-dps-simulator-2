from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from characters.registry import resolve_incoming_qte_transition_action
from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation
from simulator.transition_actions import get_transition_action, list_transition_actions


DATA_DIR = PROJECT_ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-4) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def set_concerto(sim: Simulation, character_id: str, amount: float) -> None:
    state = sim.state.character_states[character_id]
    ensure_concerto_state(state)
    state["concerto_energy"] = min(amount, state["concerto_energy_cap"])
    state["concerto_ready"] = state["concerto_energy"] >= state["concerto_energy_cap"]
    sim.state.concerto_energy[character_id] = state["concerto_energy"]


def set_qte_mode(sim: Simulation, mode: str) -> None:
    sim.transition_config["concerto_transition"]["qte_mode"] = mode


def setup_support_to_aemeath(*, qte_mode: str, aemeath_form: str = "aemeath", concerto: float = 100.0) -> Simulation:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    assert sim.execute_action("swap_to_dummy_support")
    sim.state.character_states["aemeath"]["form"] = aemeath_form
    set_concerto(sim, "dummy_support", concerto)
    set_qte_mode(sim, qte_mode)
    return sim


def test_a_default_disabled() -> None:
    sim = setup_support_to_aemeath(qte_mode="disabled")
    assert sim.transition_config["concerto_transition"]["qte_mode"] == "disabled"
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.transition_reason == "concerto_ready_qte_disabled"
    assert row.incoming_qte_applied is False
    assert row.damage == 0.0
    assert row.outgoing_concerto_consumed is False
    assert row.outgoing_concerto_after == 100.0


def test_b_dry_run() -> None:
    sim = setup_support_to_aemeath(qte_mode="dry_run")
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.transition_reason == "concerto_ready_qte_dry_run"
    assert row.incoming_qte_candidate_id == "aemeath_qte_intro_human"
    assert row.incoming_qte_applied is False
    assert row.damage == 0.0
    assert row.outgoing_concerto_consumed is False
    assert row.fallback_swap_used is True


def test_c_enabled_human_qte() -> None:
    sim = setup_support_to_aemeath(qte_mode="enabled", aemeath_form="aemeath")
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.selected_action_id == "swap_to_aemeath"
    assert row.resolved_action_id == "transition:aemeath_qte_intro_human"
    assert row.incoming_qte_candidate_id == "aemeath_qte_intro_human"
    assert row.incoming_qte_applied is True
    assert row.damage > 0.0
    assert row.scaling_stat == "atk"
    assert_close(row.action_time, 71 / 60, "human qte action_time")
    assert_close(row.combat_time_cost, 71 / 60, "human qte combat_time_cost")
    assert row.incoming_qte_damage_bonus_category == "none_or_unmodeled_intro"
    assert row.incoming_qte_trigger_classification == "qte_intro"
    assert row.incoming_qte_source_damage_label == "intro_skill_damage"
    assert row.incoming_qte_previous_outro_trigger_frame == 48
    assert row.incoming_qte_flow_light_metadata_present is True
    assert row.incoming_qte_flow_light_applied is False
    assert row.outgoing_concerto_consumed is True
    assert row.outgoing_concerto_after == 0.0
    assert row.fallback_swap_used is False
    assert "aemeath_qte_intro_human" not in sim.get_policy_action_ids()


def test_d_enabled_mech_qte() -> None:
    sim = setup_support_to_aemeath(qte_mode="enabled", aemeath_form="mech")
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "transition:aemeath_qte_intro_mech"
    assert row.incoming_qte_candidate_id == "aemeath_qte_intro_mech"
    assert row.incoming_qte_applied is True
    assert row.damage > 0.0
    assert row.scaling_stat == "atk"
    assert_close(row.action_time, 76 / 60, "mech qte action_time")
    assert_close(row.combat_time_cost, 76 / 60, "mech qte combat_time_cost")
    assert row.incoming_qte_damage_bonus_category == "resonance_skill"
    assert any(event.get("damage_bonus_category") == "resonance_skill" for event in row.transition_events)
    assert "aemeath_qte_intro_mech" not in sim.get_policy_action_ids()


def test_e_no_concerto_enabled_fallback() -> None:
    sim = setup_support_to_aemeath(qte_mode="enabled", concerto=50.0)
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.transition_type == "normal_swap"
    assert row.transition_reason == "concerto_not_ready"
    assert row.incoming_qte_applied is False
    assert row.fallback_swap_used is True
    assert row.damage == 0.0
    assert row.resolved_action_id == "swap_to_aemeath"


def test_f_cutoff() -> None:
    sim = setup_support_to_aemeath(qte_mode="enabled")
    sim.state.current_time = 119.9
    sim.state.combat_time = 119.9
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.incoming_qte_applied is True
    assert_close(sim.state.combat_time, 120.0, "cutoff combat time")
    assert row.truncated_by_combat_limit is True
    assert row.damage_after_cutoff_excluded > 0.0


def test_g_policy_action_space() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    policy_ids = sim.get_policy_action_ids()
    assert "swap_to_aemeath" in policy_ids
    assert "aemeath_qte_intro_human" not in policy_ids
    assert "aemeath_qte_intro_mech" not in policy_ids
    assert "transition:aemeath_qte_intro_human" not in policy_ids
    assert "transition:aemeath_qte_intro_mech" not in policy_ids


def test_h_generic_registry() -> None:
    actions = {record["id"] for record in list_transition_actions(DATA_DIR)}
    assert {"aemeath_qte_intro_human", "aemeath_qte_intro_mech"}.issubset(actions)
    human = get_transition_action(DATA_DIR, "aemeath_qte_intro_human")
    mech = get_transition_action(DATA_DIR, "aemeath_qte_intro_mech")
    assert human is not None and human["transition_only"] is True and human["policy_selectable"] is False
    assert mech is not None and mech["transition_only"] is True and mech["policy_selectable"] is False
    assert human["scaling_stat"] == "atk"
    assert mech["scaling_stat"] == "atk"

    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    action_id, warnings = resolve_incoming_qte_transition_action(
        "aemeath",
        sim.state.character_states["aemeath"],
        sim.transition_config,
    )
    assert action_id == "aemeath_qte_intro_human"
    assert warnings == []


def main() -> None:
    test_a_default_disabled()
    test_b_dry_run()
    test_c_enabled_human_qte()
    test_d_enabled_mech_qte()
    test_e_no_concerto_enabled_fallback()
    test_f_cutoff()
    test_g_policy_action_space()
    test_h_generic_registry()
    print("Aemeath QTE enabled transition smoke test passed.")


if __name__ == "__main__":
    main()
