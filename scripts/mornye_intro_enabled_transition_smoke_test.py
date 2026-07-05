from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation
from simulator.transition_actions import get_transition_action, transition_action_to_action_data


DATA_DIR = PROJECT_ROOT / "data"
INTRO_ID = "mornye_intro_convergence"


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


def set_mornye_intro_mode(sim: Simulation, mode: str) -> None:
    sim.transition_config["characters"]["mornye"]["intro_qte"]["mode"] = mode


def setup_aemeath_to_mornye(*, mode: str = "disabled", concerto: float = 100.0) -> Simulation:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_test_party")
    assert sim.state.active_character_id == "mornye"
    assert sim.execute_action("swap_to_aemeath")
    assert sim.state.active_character_id == "aemeath"
    set_mornye_intro_mode(sim, mode)
    set_concerto(sim, "aemeath", concerto)
    return sim


def mornye_state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["mornye"]


def test_a_default_disabled() -> None:
    sim = setup_aemeath_to_mornye(mode="disabled")
    assert sim.transition_config["characters"]["mornye"]["intro_qte"]["mode"] == "disabled"
    before_damage = sim.state.total_damage
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    assert row.selected_action_id == "swap_to_mornye"
    assert row.resolved_action_id == "swap_to_mornye"
    assert row.transition_type == "full_concerto_transition"
    assert row.transition_reason == "concerto_ready_intro_disabled"
    assert row.incoming_intro_candidate_id == INTRO_ID
    assert row.incoming_intro_mode == "disabled"
    assert row.incoming_intro_applied is False
    assert row.damage == 0.0
    assert sim.state.total_damage == before_damage
    assert row.outgoing_concerto_consumed is False
    assert row.outgoing_concerto_after == 100.0
    assert row.fallback_swap_used is True


def test_b_dry_run() -> None:
    sim = setup_aemeath_to_mornye(mode="dry_run")
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    assert row.transition_reason == "concerto_ready_intro_dry_run"
    assert row.incoming_intro_candidate_id == INTRO_ID
    assert row.incoming_intro_mode == "dry_run"
    assert row.incoming_intro_applied is False
    assert row.damage == 0.0
    assert row.outgoing_concerto_consumed is False
    assert row.fallback_swap_used is True
    assert any(event.get("incoming_intro_mode") == "dry_run" for event in row.transition_events)


def test_c_enabled_mornye_intro() -> None:
    sim = setup_aemeath_to_mornye(mode="enabled")
    mornye_state(sim)["rest_mass_energy"] = 75.0
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.selected_action_id == "swap_to_mornye"
    assert row.resolved_action_id == f"transition:{INTRO_ID}"
    assert row.incoming_intro_candidate_id == INTRO_ID
    assert row.incoming_intro_applied is True
    assert row.incoming_qte_applied is True
    assert row.damage > 0.0
    assert row.scaling_stat == "def"
    assert_close(row.action_time, 1.7, "Mornye Intro action_time")
    assert_close(row.combat_time_cost, 1.7, "Mornye Intro combat_time_cost")
    assert row.incoming_intro_damage_bonus_category == "none_or_unmodeled_intro"
    assert row.incoming_intro_trigger_classification == "intro"
    assert row.fallback_swap_used is False
    assert row.outgoing_concerto_consumed is True
    assert row.outgoing_concerto_after == 0.0
    assert row.concerto_gain == 30.0
    assert row.base_concerto_gain == 10.0
    assert row.passive_concerto_gain == 20.0
    assert row.final_concerto_gain == 30.0
    assert (row.passive_concerto_source or "").startswith("角色-女!4164")
    assert row.has_global_time_stop is False
    assert row.time_dilation_type == "时停"
    assert row.source_sheet == "角色-女"
    assert row.source_rows == [4148, 4149, 4164]
    assert state["mode"] == "wide_field_observation"
    assert state["rest_mass_energy"] == 0.0
    assert_close(state["wide_field_observation_remaining"], 30.0, "WFO remaining")
    assert_close(state["syntony_field_remaining"], 25.0, "Syntony Field remaining")
    assert row.mornye_mode_after == "wide_field_observation"
    assert row.mornye_rest_mass_after == 0.0
    assert_close(row.mornye_wfo_remaining_after or 0.0, 30.0, "logged WFO remaining")
    assert_close(row.mornye_syntony_field_remaining_after or 0.0, 25.0, "logged Syntony remaining")
    assert INTRO_ID not in sim.get_policy_action_ids()
    assert f"transition:{INTRO_ID}" not in sim.get_policy_action_ids()


def test_d_no_concerto_enabled_fallback() -> None:
    sim = setup_aemeath_to_mornye(mode="enabled", concerto=50.0)
    before_state = dict(mornye_state(sim))
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    state = mornye_state(sim)
    assert row.transition_type == "normal_swap"
    assert row.transition_reason == "concerto_not_ready"
    assert row.incoming_intro_applied is False
    assert row.fallback_swap_used is True
    assert row.damage == 0.0
    assert row.outgoing_concerto_consumed is False
    assert state["mode"] == before_state["mode"]
    assert state["wide_field_observation_remaining"] == before_state["wide_field_observation_remaining"]
    assert state["syntony_field_remaining"] == before_state["syntony_field_remaining"]


def test_e_cutoff() -> None:
    sim = setup_aemeath_to_mornye(mode="enabled")
    sim.state.current_time = 119.5
    sim.state.combat_time = 119.5
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    assert row.incoming_intro_applied is True
    assert row.truncated_by_combat_limit is True
    assert_close(sim.state.combat_time, 120.0, "cutoff combat time")
    assert row.damage_after_cutoff_excluded > 0.0


def test_f_policy_action_space() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_test_party")
    policy_ids = sim.get_policy_action_ids()
    assert "swap_to_mornye" in policy_ids
    assert INTRO_ID not in policy_ids
    assert f"transition:{INTRO_ID}" not in policy_ids


def test_g_transition_action_registry() -> None:
    record = get_transition_action(DATA_DIR, INTRO_ID)
    assert record is not None
    assert record["transition_only"] is True
    assert record["policy_selectable"] is False
    assert record["exclude_from_policy_action_space"] is True
    assert record["character_id"] == "mornye"
    assert record["transition_event_type"] == "incoming_intro_qte"
    assert record["trigger_classification"] == "intro"
    assert record["damage_bonus_category"] == "none_or_unmodeled_intro"
    assert record["element"] == "fusion"
    assert record["scaling_stat"] == "def"
    assert record["scaling_stat_source"] == "user_supplied_skill_screenshot"
    assert record["scaling_stat_source_status"] == "user_supplied_screenshot_not_embedded"
    assert "DEF-scaling" in record["scaling_stat_note"]
    assert_close(float(record["action_time"]), 1.7, "registry action_time")
    assert_close(float(record["combat_time_cost"]), 1.7, "registry combat_time_cost")
    assert record["hits"] == [2.0279]
    assert record["concerto_energy_gain"] == 30
    effects = record["mechanic_effects"]
    assert effects["clear_rest_mass_energy"] is True
    assert effects["set_mode"] == "wide_field_observation"
    assert effects["set_wide_field_observation_remaining"] == 30.0
    assert effects["set_syntony_field_remaining"] == 25.0
    assert effects["base_concerto_gain"] == 10
    assert effects["passive_concerto_gain"] == 20
    assert effects["final_concerto_gain"] == 30
    assert effects["passive_concerto_source"] == "角色-女!4164"
    assert effects["has_global_time_stop"] is False

    action = transition_action_to_action_data(record)
    assert action.id == f"transition:{INTRO_ID}"
    assert action.action_type == "swap"
    assert action.policy_selectable is False
    assert action.scaling_stat == "def"
    assert action.scaling_stat_source == "user_supplied_skill_screenshot"
    assert action.damage_element == "fusion"


def main() -> None:
    test_a_default_disabled()
    test_b_dry_run()
    test_c_enabled_mornye_intro()
    test_d_no_concerto_enabled_fallback()
    test_e_cutoff()
    test_f_policy_action_space()
    test_g_transition_action_registry()
    print("Mornye Intro enabled transition smoke test passed.")


if __name__ == "__main__":
    main()
