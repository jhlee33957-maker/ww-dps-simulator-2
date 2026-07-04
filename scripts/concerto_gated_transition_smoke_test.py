from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.resource_system import add_concerto_energy, ensure_concerto_state
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def set_concerto(sim: Simulation, character_id: str, amount: float) -> None:
    character_state = sim.state.character_states[character_id]
    ensure_concerto_state(character_state)
    character_state["concerto_energy"] = min(amount, character_state["concerto_energy_cap"])
    character_state["concerto_ready"] = character_state["concerto_energy"] >= character_state["concerto_energy_cap"]
    sim.state.concerto_energy[character_id] = character_state["concerto_energy"]


def set_qte_mode(sim: Simulation, mode: str) -> None:
    sim.transition_config["concerto_transition"]["qte_mode"] = mode


def test_a_concerto_state_initialization() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    for character_id in sim.selected_party_character_ids:
        state = sim.party_state.character_states[character_id]
        assert "concerto_energy" in state
        assert "concerto_energy_cap" in state
        assert "concerto_ready" in state
        assert_close(state["concerto_energy"], 0.0, f"{character_id} concerto start")
        assert_close(state["concerto_energy_cap"], 100.0, f"{character_id} concerto cap")
        assert state["concerto_ready"] is False


def test_b_concerto_gain() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    before = sim.state.character_states["aemeath"]["concerto_energy"]
    assert sim.execute_action("aemeath_basic_attack")
    row = sim.timeline[-1]
    after = sim.state.character_states["aemeath"]["concerto_energy"]
    assert row.concerto_before == before
    assert row.concerto_gain > 0.0
    assert after == row.concerto_after
    assert row.concerto_ready_after is False

    scratch_state = {"concerto_energy": 95.0, "concerto_energy_cap": 100.0}
    _before, gained, after, ready, wasted = add_concerto_energy(scratch_state, 20.0)
    assert gained == 5.0
    assert wasted == 15.0
    assert after == 100.0
    assert ready is True


def test_c_no_concerto_normal_swap() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    set_concerto(sim, "aemeath", 50.0)
    assert sim.execute_action("swap_to_dummy_support")
    row = sim.timeline[-1]
    assert row.transition_type == "normal_swap"
    assert row.transition_reason == "concerto_not_ready"
    assert row.outgoing_concerto_ready is False
    assert row.outgoing_concerto_consumed is False
    assert_close(row.outgoing_concerto_after, 50.0, "no-concerto swap keeps energy")
    assert row.incoming_qte_applied is False
    assert row.outgoing_outro_applied is False
    assert row.fallback_swap_used is True
    assert row.swap_timing_is_placeholder is True
    assert row.damage == 0.0
    assert row.resolved_action_id == "swap_to_dummy_support"


def test_d_full_concerto_dry_run() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    assert sim.execute_action("swap_to_dummy_support")
    set_concerto(sim, "dummy_support", 100.0)
    set_qte_mode(sim, "dry_run")
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.transition_type == "full_concerto_transition"
    assert row.transition_reason == "concerto_ready"
    assert row.incoming_qte_candidate_id in {"aemeath_qte_intro_human", "aemeath_qte_intro_mech"}
    assert row.incoming_qte_mode == "dry_run"
    assert row.incoming_qte_applied is False
    assert row.damage == 0.0
    assert row.outgoing_concerto_consumed is False
    assert_close(row.outgoing_concerto_after, 100.0, "dry-run keeps concerto")
    assert row.fallback_swap_used is True
    assert any(event.get("qte_mode") == "dry_run" for event in row.transition_events)


def test_e_full_concerto_disabled() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    assert sim.execute_action("swap_to_dummy_support")
    set_concerto(sim, "dummy_support", 100.0)
    set_qte_mode(sim, "disabled")
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.transition_type == "full_concerto_transition"
    assert row.incoming_qte_candidate_id in {"aemeath_qte_intro_human", "aemeath_qte_intro_mech"}
    assert row.incoming_qte_mode == "disabled"
    assert row.incoming_qte_applied is False
    assert row.outgoing_concerto_consumed is False
    assert_close(row.outgoing_concerto_after, 100.0, "disabled keeps concerto")


def test_f_enabled_mode_scaffold() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    assert sim.execute_action("swap_to_dummy_support")
    set_concerto(sim, "dummy_support", 100.0)
    set_qte_mode(sim, "enabled")
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.incoming_qte_mode == "enabled"
    assert row.incoming_qte_applied is False
    assert row.damage == 0.0
    assert row.outgoing_concerto_consumed is False
    assert "incoming_qte_enabled_not_implemented" in row.transition_warnings
    assert "aemeath_qte_intro_human" not in sim.get_policy_action_ids()
    assert "aemeath_qte_intro_mech" not in sim.get_policy_action_ids()


def test_g_aemeath_solo() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath")
    assert not any(action_id.startswith("swap_to_") for action_id in sim.get_policy_action_ids())
    assert all("qte" not in action_id.lower() for action_id in sim.get_policy_action_ids())


def test_h_action_mask_policy_surface() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    policy_ids = sim.get_policy_action_ids()
    assert "swap_to_aemeath" in policy_ids
    assert "swap_to_dummy_support" in policy_ids
    assert sim.is_action_available(sim.actions["swap_to_aemeath"]) is False
    assert sim.is_action_available(sim.actions["swap_to_dummy_support"]) is True
    assert "aemeath_qte_intro_human" not in policy_ids
    assert "aemeath_qte_intro_mech" not in policy_ids


def main() -> None:
    test_a_concerto_state_initialization()
    test_b_concerto_gain()
    test_c_no_concerto_normal_swap()
    test_d_full_concerto_dry_run()
    test_e_full_concerto_disabled()
    test_f_enabled_mode_scaffold()
    test_g_aemeath_solo()
    test_h_action_mask_policy_surface()
    print("Concerto-gated transition smoke test passed.")


if __name__ == "__main__":
    main()
