from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aemeath_v123_test_utils import action_snapshot, aemeath_state, make_account_sim, set_concerto_ready


def assert_close(actual: float, expected: float) -> None:
    assert abs(float(actual) - expected) < 1e-6, (actual, expected)


def execute_step(simulation, step: str, requested_action_id: str, trace: list[dict]) -> dict:
    legal_before = requested_action_id in simulation.valid_action_ids()
    assert legal_before, f"{step} was not legal"
    before = action_snapshot(simulation)
    resolved = simulation.resolve_action_id(requested_action_id)
    assert simulation.execute_action(requested_action_id), f"{step} did not execute"
    row = simulation.timeline[-1]
    after = action_snapshot(simulation)
    entry = {
        "step": step,
        "requested_action": requested_action_id,
        "pre_execution_resolved_action": resolved,
        "resolved_action": row.resolved_action_id,
        "legal_before_execution": legal_before,
        "fallback_swap_used": bool(row.fallback_swap_used),
    }
    for key, value in before.items():
        entry[f"{key}_before"] = value
        entry[f"{key}_after"] = after[key]
    trace.append(entry)
    return entry


def main() -> None:
    simulation = make_account_sim()
    state = aemeath_state(simulation)
    assert simulation.state.active_character_id == "mornye"
    assert simulation.state.mechanics_config["aemeath"]["aemeath_resonance_mode"] == "tune_rupture"
    assert action_snapshot(simulation) == {
        "combat_time": 0.0,
        "form": "aemeath",
        "aemeath_combo_stage": 1,
        "mech_combo_stage": 1,
        "synchronization_rate": 0.0,
        "resonance_rate": 0.0,
        "seraphic_duo_remaining": 0.0,
        "starlume_acceleration_remaining": 0.0,
        "instant_response": False,
        "instant_response_consumed": False,
        "radiance_ready": True,
        "finale_available": False,
    }

    early_radiance_setup_trace: list[dict] = []
    generic_swap_in = execute_step(simulation, "generic swap to Aemeath", "swap_to_aemeath", early_radiance_setup_trace)
    assert generic_swap_in["fallback_swap_used"] is True
    assert_close(state["starlume_acceleration_remaining"], 0.0)
    early_heavy = execute_step(simulation, "early charged-II Heavy", "aemeath_heavy_attack", early_radiance_setup_trace)
    assert early_heavy["resolved_action"] == "aemeath_heavy_aemeath_charged_2"
    assert state["account_radiance_quick_charge_ready"] is False
    assert_close(state["synchronization_rate"], 100.0)
    assert state["aemeath_combo_stage"] == 3
    assert_close(state["starlume_acceleration_remaining"], 0.0)
    generic_swap_out = execute_step(simulation, "generic swap back to Mornye", "swap_to_mornye", early_radiance_setup_trace)
    assert generic_swap_out["fallback_swap_used"] is True
    assert state["aemeath_combo_stage"] == 3
    assert_close(state["starlume_acceleration_remaining"], 0.0)

    support_transition_trace: list[dict] = []
    set_concerto_ready(simulation, "mornye")
    mornye_to_lynae = execute_step(simulation, "Mornye to Lynae", "swap_to_lynae", support_transition_trace)
    assert mornye_to_lynae["resolved_action"] == "transition:lynae_intro_time_to_show_some_colors"
    set_concerto_ready(simulation, "lynae")
    lynae_to_aemeath = execute_step(simulation, "Lynae Outro to Aemeath Intro", "swap_to_aemeath", support_transition_trace)
    assert lynae_to_aemeath["resolved_action"] == "transition:aemeath_qte_intro_human"
    assert state["form"] == "aemeath"
    assert state["aemeath_combo_stage"] == 3
    assert_close(state["synchronization_rate"], 100.0)
    assert_close(state["starlume_acceleration_remaining"], 15.0)
    assert state["account_radiance_quick_charge_ready"] is False

    aemeath_main_window_trace: list[dict] = []
    expected_actions = [
        ("Basic stage 3", "aemeath_basic_attack", "aemeath_basic_form_stage_3"),
        ("Basic stage 4", "aemeath_basic_attack", "aemeath_basic_form_stage_4"),
        ("First Liberation", "aemeath_resonance_liberation", "aemeath_liberation_overdrive"),
        ("First enhanced Skill", "aemeath_resonance_skill", "aemeath_seraphic_duet_encore"),
        ("Basic stage 2", "aemeath_basic_attack", "aemeath_basic_form_stage_2"),
        ("Basic stage 3", "aemeath_basic_attack", "aemeath_basic_form_stage_3"),
        ("Basic stage 4", "aemeath_basic_attack", "aemeath_basic_form_stage_4"),
        ("Second enhanced Skill", "aemeath_resonance_skill", "aemeath_seraphic_duet_overturn"),
        ("Mech charged-II Heavy", "aemeath_heavy_attack", "aemeath_heavy_mech_charged_2"),
        ("Heavenfall Finale", "aemeath_resonance_liberation", "aemeath_heavenfall_finale"),
    ]
    for step, requested_action_id, expected_resolved_action in expected_actions:
        entry = execute_step(simulation, step, requested_action_id, aemeath_main_window_trace)
        assert entry["resolved_action"] == expected_resolved_action

    assert len(aemeath_main_window_trace) == 10
    assert [entry["requested_action"] for entry in aemeath_main_window_trace[:2]] == ["aemeath_basic_attack"] * 2
    assert [entry["resolved_action"] for entry in aemeath_main_window_trace[:2]] == [
        "aemeath_basic_form_stage_3",
        "aemeath_basic_form_stage_4",
    ]
    first_stage_four = aemeath_main_window_trace[1]
    assert_close(first_stage_four["synchronization_rate_after"], 139.97)
    assert_close(first_stage_four["resonance_rate_after"], 0.0)
    assert first_stage_four["seraphic_duo_remaining_after"] > 0.0

    first_liberation = aemeath_main_window_trace[2]
    assert first_liberation["form_after"] == "mech"
    assert first_liberation["mech_combo_stage_after"] == 2
    assert_close(first_liberation["synchronization_rate_after"], 169.97)
    assert_close(first_liberation["resonance_rate_after"], 2.0)
    assert_close(first_liberation["starlume_acceleration_remaining_after"], 0.0)

    first_enhanced_skill = aemeath_main_window_trace[3]
    assert first_enhanced_skill["resolved_action"] == "aemeath_seraphic_duet_encore"
    assert first_enhanced_skill["form_after"] == "aemeath"
    assert first_enhanced_skill["aemeath_combo_stage_after"] == 2
    assert_close(first_enhanced_skill["synchronization_rate_after"], 69.97)
    assert_close(first_enhanced_skill["resonance_rate_after"], 3.0)
    assert_close(first_enhanced_skill["seraphic_duo_remaining_after"], 0.0)

    second_basic_segment = aemeath_main_window_trace[4:7]
    assert len(second_basic_segment) == 3
    assert [entry["resolved_action"] for entry in second_basic_segment] == [
        "aemeath_basic_form_stage_2",
        "aemeath_basic_form_stage_3",
        "aemeath_basic_form_stage_4",
    ]
    second_stage_four = second_basic_segment[-1]
    assert second_stage_four["aemeath_combo_stage_after"] == 1
    assert second_stage_four["seraphic_duo_remaining_after"] > 0.0
    assert_close(second_stage_four["synchronization_rate_after"], 116.38)
    assert_close(second_stage_four["resonance_rate_after"], 3.0)

    second_enhanced_skill = aemeath_main_window_trace[7]
    assert second_enhanced_skill["resolved_action"] == "aemeath_seraphic_duet_overturn"
    assert second_enhanced_skill["form_after"] == "mech"
    assert second_enhanced_skill["mech_combo_stage_after"] == 2
    assert second_enhanced_skill["instant_response_after"] is True
    assert_close(second_enhanced_skill["synchronization_rate_after"], 16.38)
    assert_close(second_enhanced_skill["resonance_rate_after"], 4.0)
    assert_close(second_enhanced_skill["seraphic_duo_remaining_after"], 0.0)

    heavy = aemeath_main_window_trace[8]
    assert heavy["resolved_action"] == "aemeath_heavy_mech_charged_2"
    assert heavy["instant_response_before"] is True
    assert heavy["instant_response_after"] is False
    assert heavy["instant_response_consumed_after"] is True
    assert_close(heavy["synchronization_rate_after"], 200.0)
    assert_close(heavy["resonance_rate_after"], 4.0)
    assert heavy["finale_available_after"] is True

    finale = aemeath_main_window_trace[9]
    assert finale["resolved_action"] == "aemeath_heavenfall_finale"

    assert simulation.state.mechanics_config["aemeath"]["aemeath_resonance_mode"] == "tune_rupture"
    assert not state["fusion_trail_event_log"]
    assert state["fusion_effect_stacks"] == 0
    assert len(simulation.get_policy_action_ids()) == 25
    all_trace = early_radiance_setup_trace + support_transition_trace + aemeath_main_window_trace
    assert sum(not entry["legal_before_execution"] for entry in all_trace) == 0
    assert sum(entry["fallback_swap_used"] for entry in early_radiance_setup_trace) == 2
    assert sum(entry["fallback_swap_used"] for entry in support_transition_trace + aemeath_main_window_trace) == 0
    print(json.dumps({"early_radiance_setup_trace": early_radiance_setup_trace}, ensure_ascii=True, sort_keys=True))
    print(json.dumps({"support_transition_trace": support_transition_trace}, ensure_ascii=True, sort_keys=True))
    print(json.dumps({"aemeath_main_window_trace": aemeath_main_window_trace}, ensure_ascii=True, sort_keys=True))
    print(
        "aemeath_account_cycle_feasibility_v123_smoke_test ok "
        "invalid=0 unexpected_fallback=0 requested_generic_swap_transitions=2"
    )


if __name__ == "__main__":
    main()
