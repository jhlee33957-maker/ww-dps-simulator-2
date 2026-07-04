from __future__ import annotations

import math
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.party_transition import PLACEHOLDER_WARNING
from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"
QTE_REVIEW_PATH = DATA_DIR / "extracted" / "aemeath_qte_intro_outro_candidates.json"
QTE_ACTION_CANDIDATE_PATH = DATA_DIR / "extracted" / "aemeath_qte_action_candidates.json"


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
    assert sim.transition_config["characters"]["aemeath"]["intro_qte"]["enabled"] is False
    assert sim.transition_config["characters"]["aemeath"]["intro_qte"]["mode"] == "disabled"
    assert sim.transition_config["characters"]["aemeath"]["intro_qte"]["implementation_status"] == "review_only"
    assert sim.transition_config["characters"]["aemeath"]["outro"]["enabled"] is False
    assert sim.transition_config["concerto_transition"]["qte_mode"] == "disabled"
    assert all("qte" not in action_id.lower() for action_id in sim.get_policy_action_ids())
    if QTE_REVIEW_PATH.exists():
        qte_review = json.loads(QTE_REVIEW_PATH.read_text(encoding="utf-8"))
        assert qte_review["review_only"] is True
        assert qte_review["simulation_applied"] is False
        assert qte_review["candidate_count"] > 0
        assert any("qte" in group["group_id"] for group in qte_review["groups"])
    if QTE_ACTION_CANDIDATE_PATH.exists():
        qte_action_candidates = json.loads(QTE_ACTION_CANDIDATE_PATH.read_text(encoding="utf-8"))
        assert qte_action_candidates["review_only"] is True
        assert qte_action_candidates["simulation_applied"] is False
        assert qte_action_candidates["simulation_executable"] is False
        assert qte_action_candidates["executable_policy_action_count"] == 0
        candidate_ids = {candidate["proposed_action_id"] for candidate in qte_action_candidates["candidates"]}
        assert "aemeath_qte_intro_human" not in sim.get_policy_action_ids()
        assert "aemeath_qte_intro_mech" not in sim.get_policy_action_ids()
        assert candidate_ids.issubset({"aemeath_qte_intro_human", "aemeath_qte_intro_mech"})
        for candidate in qte_action_candidates["candidates"]:
            assert candidate["simulation_executable"] is False
            assert candidate["policy_selectable"] is False
            assert candidate["damage_candidate"]["trigger_classification"] == "qte_intro"
            assert "damage_bonus_category" in candidate["damage_candidate"]
            assert candidate["proposed_action_id"] not in sim.get_policy_action_ids()
        assert all(
            candidate["proposed_action_id"] not in sim.get_policy_action_ids()
            for candidate in qte_action_candidates["candidates"]
        )
    assert_close(sim.actions["swap_to_aemeath"].action_time or 0.0, 0.5, "swap_to_aemeath action_time")
    assert_close(sim.actions["swap_to_aemeath"].combat_time_cost or 0.0, 0.5, "swap_to_aemeath combat_time_cost")

    assert sim.execute_action("swap_to_dummy_support")
    first_swap = sim.timeline[-1]
    assert first_swap.outgoing_character_id == "aemeath"
    assert first_swap.incoming_character_id == "dummy_support"
    assert first_swap.transition_type == "normal_swap"
    assert first_swap.transition_reason == "concerto_not_ready"
    assert first_swap.transition_events == []
    assert first_swap.incoming_intro_event_id is None
    assert first_swap.fallback_swap_used is True
    assert first_swap.swap_timing_is_placeholder is True
    assert first_swap.swap_timing_source == "party_presets.aemeath_test_party.generic_swap"
    assert PLACEHOLDER_WARNING in first_swap.transition_warnings
    assert_close(first_swap.action_time, 0.5, "first swap action_time")
    assert_close(first_swap.combat_time_cost, 0.5, "first swap combat_time_cost")

    assert first_swap.incoming_qte_applied is False

    assert sim.execute_action("swap_to_aemeath")
    no_concerto_swap = sim.timeline[-1]
    assert no_concerto_swap.transition_type == "normal_swap"
    assert no_concerto_swap.transition_reason == "concerto_not_ready"
    assert no_concerto_swap.outgoing_outro_event_id is None
    assert no_concerto_swap.outgoing_outro_applied is False
    assert no_concerto_swap.transition_events == []

    assert sim.execute_action("swap_to_dummy_support")
    set_full_concerto(sim, "dummy_support")
    assert sim.execute_action("swap_to_aemeath")
    outro_swap = sim.timeline[-1]
    assert outro_swap.outgoing_character_id == "dummy_support"
    assert outro_swap.incoming_character_id == "aemeath"
    assert outro_swap.transition_type == "full_concerto_transition"
    assert outro_swap.transition_reason == "concerto_ready"
    assert outro_swap.outgoing_outro_event_id == "dummy_support_outro_damage_amp"
    assert outro_swap.outgoing_outro_applied is True
    assert outro_swap.incoming_qte_candidate_id in {"aemeath_qte_intro_human", "aemeath_qte_intro_mech"}
    assert outro_swap.incoming_qte_mode == "disabled"
    assert outro_swap.incoming_qte_applied is False
    assert outro_swap.incoming_intro_event_id is None
    assert outro_swap.fallback_swap_used is True
    assert outro_swap.swap_timing_is_placeholder is True
    assert_close(outro_swap.action_time, 0.5, "outro fallback action_time")
    assert_close(outro_swap.combat_time_cost, 0.5, "outro fallback combat_time_cost")
    assert len(outro_swap.transition_events) == 1
    event = outro_swap.transition_events[0]
    assert event["event_type"] == "outro"
    assert event["action_time"] == 0.0
    assert event["combat_time_cost"] == 0.0
    assert event["implementation_status"] == "test_only"
    assert event["applies_buffs"] == ["dummy_support_outro_damage_amp"]
    assert "dummy_support_outro_damage_amp" in outro_swap.applied_buffs
    assert "dummy_support_outro_damage_amp" in outro_swap.active_buffs

    print("QTE / Intro / Outro foundation smoke test passed.")


if __name__ == "__main__":
    main()
