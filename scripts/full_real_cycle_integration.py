from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.damage_attribution import (  # noqa: E402
    DamageAttributionError,
    event_identity,
    row_damage_attribution,
)
from simulator.simulation import Simulation


SCHEMA_VERSION = "full_real_cycle_integration_v1"
BASELINE_LABEL = "103"
BASELINE_ARCHIVE = "ww-dps-simulator-2(103).zip"
CANDIDATE_LABEL = "104"
PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
INITIAL_ACTIVE_CHARACTER = "aemeath"
FRAME_RATE = 60
EXPECTED_FINAL_COMBAT_TIME = 32.95
EXPECTED_FINAL_COMBAT_FRAMES = 1977
FLOAT_TOLERANCE = 1e-9
FRAME_TOLERANCE = 1.0 / FRAME_RATE + 1e-9

SELECTED_ROUTE = [
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_resonance_skill",
    "swap_to_mornye",
    "mornye_resonance_skill",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_heavy_attack",
    "mornye_resonance_liberation",
    "mornye_echo_reactor_husk",
    "mornye_resonance_skill",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_heavy_attack",
    "swap_to_lynae",
    "lynae_resonance_skill",
    "lynae_spark_collision",
    "lynae_polychrome_leap",
    "lynae_polychrome_leap",
    "lynae_polychrome_leap",
    "lynae_visual_impact",
    "lynae_resonance_liberation",
    "lynae_echo_hyvatia",
    "swap_to_aemeath",
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_tune_break",
    "aemeath_resonance_liberation",
    "aemeath_echo_sigillum",
    "aemeath_resonance_skill",
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_resonance_skill",
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_resonance_skill",
]

EXPECTED_RESOLVED_ROUTE = [
    "aemeath_basic_form_stage_1",
    "aemeath_basic_form_stage_2",
    "aemeath_basic_form_stage_3",
    "aemeath_basic_form_stage_4",
    "aemeath_sync_strike_armament_merge",
    "swap_to_mornye",
    "mornye_skill_expectation_error",
    "mornye_basic_stage_1",
    "mornye_basic_stage_2",
    "mornye_basic_stage_3",
    "mornye_heavy_geopotential_shift",
    "mornye_liberation_critical_protocol",
    "mornye_echo_reactor_husk",
    "mornye_skill_distributed_array",
    "mornye_wfo_basic_stage_1",
    "mornye_wfo_basic_stage_2",
    "mornye_wfo_basic_stage_3",
    "mornye_heavy_inversion",
    "transition:lynae_intro_time_to_show_some_colors",
    "lynae_resonance_skill_palette",
    "lynae_spark_collision_lv3",
    "lynae_polychrome_leap_stage_1",
    "lynae_polychrome_leap_stage_2",
    "lynae_polychrome_leap_stage_3",
    "lynae_visual_impact",
    "lynae_resonance_liberation_prismatic_overblast",
    "lynae_echo_hyvatia",
    "transition:aemeath_qte_intro_mech",
    "aemeath_mech_basic_stage_2",
    "aemeath_mech_basic_stage_3",
    "aemeath_tune_break",
    "aemeath_liberation_overdrive",
    "aemeath_echo_sigillum",
    "aemeath_form_switch_to_aemeath_after_overdrive",
    "aemeath_basic_form_stage_3",
    "aemeath_basic_form_stage_4",
    "aemeath_seraphic_duet_overturn",
    "aemeath_mech_basic_stage_2",
    "aemeath_mech_basic_stage_3",
    "aemeath_mech_basic_stage_4",
    "aemeath_seraphic_duet_encore",
]


class IntegrationFailure(AssertionError):
    pass


@dataclass
class FullCycleRun:
    simulation: Simulation
    result: dict[str, Any]


def assert_close(actual: float, expected: float, label: str, tolerance: float = FLOAT_TOLERANCE) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance):
        raise IntegrationFailure(f"{label}: expected {expected}, got {actual}")


def build_simulation() -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        party=PARTY_ID,
        initial_active_character=INITIAL_ACTIVE_CHARACTER,
    )


def _state_snapshot(sim: Simulation) -> dict[str, Any]:
    state = sim.state
    return {
        "current_time": state.current_time,
        "combat_time": state.combat_time,
        "active_character_id": state.active_character_id,
        "enemy_off_tune_current": state.enemy_off_tune_current,
        "enemy_tune_break_available": state.enemy_tune_break_available,
        "enemy_tune_break_cooldown_remaining": state.enemy_tune_break_cooldown_remaining,
        "interfered_marker_remaining": state.interfered_marker_remaining,
        "interfered_marker_damage_taken_amp": state.interfered_marker_damage_taken_amp,
        "rupturous_trail_stacks": state.rupturous_trail_stacks,
        "rupturous_trail_remaining": state.rupturous_trail_remaining,
        "resonance_energy": dict(state.resonance_energy),
        "concerto_energy": dict(state.concerto_energy),
        "wasted_concerto_energy": dict(state.wasted_concerto_energy),
        "cooldowns": dict(state.cooldowns),
        "scheduled_effects": [
            effect.model_dump(mode="json") if hasattr(effect, "model_dump") else dict(effect)
            for effect in state.scheduled_effects
        ],
    }


def _pre_resolved_id(sim: Simulation, action_id: str) -> str:
    action = sim.policy_actions[action_id]
    if action.action_type == "swap":
        return f"transition_request:{action_id}"
    return sim.resolve_action(action).id


def _diagnostic(
    sim: Simulation,
    *,
    step_index: int,
    selected_action_id: str,
    expected_resolved_action_id: str,
    actual_resolved_action_id: str | None = None,
    reason: str,
) -> str:
    state = sim.state
    return json.dumps(
        {
            "reason": reason,
            "step": step_index,
            "selected_action_id": selected_action_id,
            "expected_resolved_action_id": expected_resolved_action_id,
            "actual_resolved_action_id": actual_resolved_action_id,
            "current_time": state.current_time,
            "combat_time": state.combat_time,
            "active_character_id": state.active_character_id,
            "enemy_off_tune_current": state.enemy_off_tune_current,
            "enemy_tune_break_available": state.enemy_tune_break_available,
            "enemy_tune_break_cooldown_remaining": state.enemy_tune_break_cooldown_remaining,
            "interfered_marker_remaining": state.interfered_marker_remaining,
            "rupturous_trail_stacks": state.rupturous_trail_stacks,
            "rupturous_trail_remaining": state.rupturous_trail_remaining,
            "resonance_energy": dict(state.resonance_energy),
            "concerto_energy": dict(state.concerto_energy),
            "cooldowns": dict(state.cooldowns),
            "valid_policy_actions": sim.valid_action_ids(),
        },
        ensure_ascii=False,
        indent=2,
    )


def _compact_event(event: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "event_type",
        "combat_time",
        "scheduled_effect_id",
        "scheduled_effect_instance_id",
        "payload_action_id",
        "source_action_id",
        "source_character_id",
        "host_action_id",
        "host_combat_start_time",
        "host_combat_end_time",
        "host_action_combat_offset",
        "damage",
        "base_resonance_energy_gain",
        "final_resonance_energy_gain",
        "resonance_energy_gain",
        "concerto_energy_gain",
        "off_tune_gain",
        "off_tune_value",
        "damage_category",
        "damage_bonus_category",
        "damage_element",
        "scaling_stat",
        "scaling_value",
        "source_ref",
        "trigger_index",
        "scheduled_effect_local_trigger_index",
    ]
    return {key: event.get(key) for key in keys if key in event}


def _event_identity(collection_name: str, event: dict[str, Any]) -> tuple[Any, ...]:
    return event_identity(collection_name, event)


def _sourced_damage_collections(row: Any) -> list[tuple[str, list[dict[str, Any]]]]:
    return [
        ("scheduled_damage_events", list(getattr(row, "scheduled_damage_events", []) or [])),
        ("tune_response_events", list(getattr(row, "tune_response_events", []) or [])),
        (
            "generated_mechanic_damage_events",
            list(getattr(row, "generated_mechanic_damage_events", []) or []),
        ),
    ]


def _row_actor_id(row: Any) -> str:
    return str(row.actor_character_id or row.character_id or row.active_character_before or "unknown")


def _row_damage_attribution(row: Any) -> dict[str, Any]:
    try:
        return row_damage_attribution(row, tolerance=FLOAT_TOLERANCE)
    except DamageAttributionError as exc:
        raise IntegrationFailure(str(exc)) from exc


def _per_character_damage(sim: Simulation) -> dict[str, float]:
    totals: defaultdict[str, float] = defaultdict(float)
    for row in sim.timeline:
        attribution = _row_damage_attribution(row)
        for source, damage in attribution["damage_by_character"].items():
            totals[source] += damage
    return dict(sorted(totals.items()))


def _action_counts(steps: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "selected": dict(Counter(step["selected_action_id"] for step in steps)),
        "resolved": dict(Counter(step["resolved_action_id"] for step in steps)),
        "policy_action_count": len(steps),
    }


def _build_step_record(
    *,
    step_index: int,
    selected_action_id: str,
    expected_resolved_action_id: str,
    pre_resolved_action_id: str,
    before: dict[str, Any],
    after: dict[str, Any],
    row: Any,
) -> dict[str, Any]:
    row_data = row.model_dump(mode="json")
    return {
        "step": step_index,
        "selected_action_id": selected_action_id,
        "pre_resolved_action_id": pre_resolved_action_id,
        "expected_resolved_action_id": expected_resolved_action_id,
        "resolved_action_id": row.resolved_action_id,
        "availability": True,
        "active_character_before": before["active_character_id"],
        "active_character_after": after["active_character_id"],
        "current_time_before": before["current_time"],
        "current_time_after": after["current_time"],
        "combat_time_before": before["combat_time"],
        "combat_time_after": after["combat_time"],
        "action_time": row.action_time,
        "combat_time_cost": row.combat_time_cost,
        "effective_combat_time_cost": row.effective_combat_time_cost,
        "damage": row.damage,
        "direct_action_damage": row.direct_action_damage,
        "generated_mechanic_damage": row.generated_mechanic_damage,
        "scheduled_damage": row.scheduled_damage,
        "cooldowns": {
            "before": before["cooldowns"],
            "after": after["cooldowns"],
        },
        "resonance_energy": {
            "before": before["resonance_energy"],
            "after": after["resonance_energy"],
            "base_gain": row.base_resonance_energy_gain,
            "final_gain": row.final_resonance_energy_gain,
            "gained": row.resonance_energy_gained,
            "wasted": row.resonance_energy_wasted,
        },
        "concerto_energy": {
            "before": before["concerto_energy"],
            "after": after["concerto_energy"],
            "base_gain": row.base_concerto_gain,
            "final_gain": row.final_concerto_gain,
            "gained": row.concerto_energy_gained,
            "wasted": row.concerto_energy_wasted,
            "wasted_total_after": after["wasted_concerto_energy"],
        },
        "off_tune": {
            "before": before["enemy_off_tune_current"],
            "after": after["enemy_off_tune_current"],
            "row_before": row.enemy_off_tune_current_before,
            "row_after": row.enemy_off_tune_current_after,
            "value": row.off_tune_value,
            "added": row.off_tune_added,
            "source_status": row.off_tune_value_source_status,
            "source_ref": row.off_tune_value_source_ref,
        },
        "tune_break": {
            "available_before": before["enemy_tune_break_available"],
            "available_after": after["enemy_tune_break_available"],
            "cooldown_before": before["enemy_tune_break_cooldown_remaining"],
            "cooldown_after": after["enemy_tune_break_cooldown_remaining"],
            "enemy_off_tune_current_after_tune_break": row.enemy_off_tune_current_after_tune_break,
            "party_response_scan_triggered": row.party_response_scan_triggered,
            "tune_response_events": getattr(row, "tune_response_events", []),
        },
        "interfered_marker": {
            "remaining_before": before["interfered_marker_remaining"],
            "remaining_after": after["interfered_marker_remaining"],
            "damage_taken_amp_before": before["interfered_marker_damage_taken_amp"],
            "damage_taken_amp_after": after["interfered_marker_damage_taken_amp"],
            "newly_applied_this_action": row.interfered_marker_newly_applied_this_action,
        },
        "rupturous_trail": {
            "stacks_before": before["rupturous_trail_stacks"],
            "stacks_after": after["rupturous_trail_stacks"],
            "remaining_before": before["rupturous_trail_remaining"],
            "remaining_after": after["rupturous_trail_remaining"],
            "gain_events": row.aemeath_rupturous_trail_gain_events,
            "seraphic_snapshot": row.aemeath_seraphic_duet_trail_stack_snapshot,
            "seraphic_stack_factor": row.aemeath_seraphic_duet_trail_stack_factor,
            "seraphic_preservation_active": row.aemeath_seraphic_duet_trail_preservation_active,
            "seraphic_consumed": row.aemeath_seraphic_duet_trail_consumed,
            "seraphic_total_extra_tune_multiplier": row.aemeath_seraphic_duet_total_extra_tune_multiplier,
            "forte_stacks_before": row.aemeath_forte_enhancement_stacks_before,
            "forte_stacks_consumed": row.aemeath_forte_enhancement_stacks_consumed,
            "forte_stacks_after": row.aemeath_forte_enhancement_stacks_after,
            "trail_no_cost_consumed": row.aemeath_trail_no_cost_consumed,
        },
        "transition": {
            "transition_type": row.transition_type,
            "outgoing_outro_event_id": row.outgoing_outro_event_id,
            "incoming_intro_event_id": row.incoming_intro_event_id,
            "fallback_swap_used": row.fallback_swap_used,
            "swap_timing_is_placeholder": row.swap_timing_is_placeholder,
            "swap_timing_source": row.swap_timing_source,
            "applied_buffs": row.applied_buffs,
        },
        "echo_scheduled_event_data": {
            "sigillum_activation_scheduled": row.aemeath_sigillum_activation_scheduled,
            "sigillum_hit_schedule_events": row.aemeath_sigillum_hit_schedule_events,
        },
        "scheduled_events": {
            "damage": [_compact_event(event) for event in row.scheduled_damage_events],
            "healing": [_compact_event(event) for event in row.scheduled_healing_events],
            "status_application": [_compact_event(event) for event in row.scheduled_status_application_events],
        },
        "row": row_data,
    }


def execute_strict_route() -> FullCycleRun:
    if "short_wait" in SELECTED_ROUTE:
        raise IntegrationFailure("short_wait is forbidden in the selected route")
    sim = build_simulation()
    steps: list[dict[str, Any]] = []
    for index, (selected_action_id, expected_resolved_action_id) in enumerate(
        zip(SELECTED_ROUTE, EXPECTED_RESOLVED_ROUTE, strict=True),
        start=1,
    ):
        if selected_action_id not in sim.policy_actions:
            raise IntegrationFailure(
                _diagnostic(
                    sim,
                    step_index=index,
                    selected_action_id=selected_action_id,
                    expected_resolved_action_id=expected_resolved_action_id,
                    reason="selected action is not a policy action",
                )
            )
        selected_action = sim.policy_actions[selected_action_id]
        pre_resolved_action_id = _pre_resolved_id(sim, selected_action_id)
        available = sim.is_action_available(selected_action)
        if not available:
            raise IntegrationFailure(
                _diagnostic(
                    sim,
                    step_index=index,
                    selected_action_id=selected_action_id,
                    expected_resolved_action_id=expected_resolved_action_id,
                    actual_resolved_action_id=pre_resolved_action_id,
                    reason="selected policy action is unavailable",
                )
            )
        before = _state_snapshot(sim)
        ok = sim.execute_action(selected_action_id)
        if not ok or not sim.timeline:
            raise IntegrationFailure(
                _diagnostic(
                    sim,
                    step_index=index,
                    selected_action_id=selected_action_id,
                    expected_resolved_action_id=expected_resolved_action_id,
                    actual_resolved_action_id=pre_resolved_action_id,
                    reason="execute_action returned false",
                )
            )
        row = sim.timeline[-1]
        if row.selected_action_id != selected_action_id:
            raise IntegrationFailure(
                _diagnostic(
                    sim,
                    step_index=index,
                    selected_action_id=selected_action_id,
                    expected_resolved_action_id=expected_resolved_action_id,
                    actual_resolved_action_id=row.resolved_action_id,
                    reason=f"selected action changed to {row.selected_action_id}",
                )
            )
        if row.resolved_action_id != expected_resolved_action_id:
            raise IntegrationFailure(
                _diagnostic(
                    sim,
                    step_index=index,
                    selected_action_id=selected_action_id,
                    expected_resolved_action_id=expected_resolved_action_id,
                    actual_resolved_action_id=row.resolved_action_id,
                    reason="resolved action mismatch",
                )
            )
        if row.resolved_action_id == "short_wait":
            raise IntegrationFailure("short_wait appeared in the resolved route")
        after = _state_snapshot(sim)
        steps.append(
            _build_step_record(
                step_index=index,
                selected_action_id=selected_action_id,
                expected_resolved_action_id=expected_resolved_action_id,
                pre_resolved_action_id=pre_resolved_action_id,
                before=before,
                after=after,
                row=row,
            )
        )
    result = build_result(sim, steps)
    return FullCycleRun(simulation=sim, result=result)


def build_result(sim: Simulation, steps: list[dict[str, Any]]) -> dict[str, Any]:
    summary = sim.summary()
    scheduled_events = [_compact_event(event) for event in sim.state.scheduled_effect_event_log]
    fallback_steps = [
        {
            "step": step["step"],
            "selected_action_id": step["selected_action_id"],
            "resolved_action_id": step["resolved_action_id"],
            "fallback_swap_used": step["transition"]["fallback_swap_used"],
            "swap_timing_is_placeholder": step["transition"]["swap_timing_is_placeholder"],
            "transition_type": step["transition"]["transition_type"],
        }
        for step in steps
        if step["transition"]["fallback_swap_used"] or step["transition"]["swap_timing_is_placeholder"]
    ]
    per_character_damage = _per_character_damage(sim)
    total_damage = sim.state.total_damage
    final_combat_time = sim.state.combat_time
    damage_attribution = [_row_damage_attribution(row) for row in sim.timeline]
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate": {
            "baseline_label": BASELINE_LABEL,
            "baseline_archive": BASELINE_ARCHIVE,
            "candidate_label": CANDIDATE_LABEL,
            "external_review_status": "pending",
            "route_status": "implemented_tests_passed_pending_external_review",
            "not_120_second_baseline": True,
        },
        "party": {
            "party_id": PARTY_ID,
            "initial_active_character": INITIAL_ACTIVE_CHARACTER,
            "selected_party_character_ids": list(sim.selected_party_character_ids),
            "active_build_profiles": dict(sim.active_build_profiles),
            "build_profile_validation": dict(sim.build_profile_validation),
        },
        "selected_action_sequence": list(SELECTED_ROUTE),
        "resolved_action_sequence": [step["resolved_action_id"] for step in steps],
        "steps": steps,
        "scheduled_effect_event_data": scheduled_events,
        "damage_attribution": damage_attribution,
        "remaining_scheduled_effects": [
            effect.model_dump(mode="json") if hasattr(effect, "model_dump") else dict(effect)
            for effect in sim.state.scheduled_effects
        ],
        "totals": {
            "total_damage": total_damage,
            "final_combat_time": final_combat_time,
            "final_combat_frames": round(final_combat_time * FRAME_RATE),
            "route_duration_dps_not_120_second_baseline": total_damage / final_combat_time,
            "simulation_summary_dps_over_120_seconds": summary.dps,
            "damage_by_character": per_character_damage,
            "damage_by_selected_action": summary.damage_by_selected_action,
            "damage_by_resolved_action": summary.damage_by_resolved_action,
            "action_counts": _action_counts(steps),
        },
        "checkpoint_values": collect_checkpoints(steps, sim),
        "placeholder_fallback": {
            "count": len(fallback_steps),
            "locations": fallback_steps,
            "known_limit": (
                "Only the opening Aemeath -> Mornye normal swap uses the current generic 0.50-second "
                "placeholder timing. The route is mechanically complete but not fully source-exact in "
                "absolute timing until that normal-swap timing is resolved."
            ),
        },
        "unresolved_limits": [
            "Opening Aemeath -> Mornye normal-swap exact timing is unresolved; current route uses the known 0.50s placeholder.",
            "Mornye exact dodge-cancel next-input frame remains unresolved; Reactor Husk uses the verified uncancelled 66F route.",
            "Mornye/Aemeath/Lynae active Echo Off-Tune values are source-unconfirmed and remain runtime zero where unresolved.",
        ],
        "determinism_signature": determinism_signature(sim, steps),
    }


def collect_checkpoints(steps: list[dict[str, Any]], sim: Simulation) -> dict[str, Any]:
    by_step = {step["step"]: step for step in steps}
    return {
        "aemeath_opening": {
            "after_step_5_enemy_off_tune": by_step[5]["off_tune"]["after"],
            "opening_swap": by_step[6]["transition"],
        },
        "mornye_segment": {
            "liberation_step": by_step[12],
            "reactor_husk_step": by_step[13],
            "after_step_18_enemy_off_tune": by_step[18]["off_tune"]["after"],
            "after_step_18_mornye_concerto": by_step[18]["concerto_energy"]["after"]["mornye"],
        },
        "lynae_segment": {
            "after_intro_concerto": by_step[19]["concerto_energy"]["after"]["lynae"],
            "concerto_by_step": {
                str(index): by_step[index]["concerto_energy"]["after"]["lynae"]
                for index in range(19, 28)
            },
            "off_tune_by_step": {
                str(index): by_step[index]["off_tune"]["after"]
                for index in range(19, 28)
            },
            "wasted_concerto_after_liberation": by_step[26]["concerto_energy"]["wasted_total_after"]["lynae"],
        },
        "lynae_to_aemeath_transition": by_step[28]["transition"],
        "tune_break": by_step[31],
        "overdrive": by_step[32],
        "sigillum": by_step[33],
        "first_seraphic_duet": by_step[37],
        "second_seraphic_duet": by_step[41],
        "final_state": {
            "combat_time": sim.state.combat_time,
            "combat_frames": round(sim.state.combat_time * FRAME_RATE),
            "enemy_off_tune_current": sim.state.enemy_off_tune_current,
            "interfered_marker_remaining": sim.state.interfered_marker_remaining,
            "rupturous_trail_stacks": sim.state.rupturous_trail_stacks,
            "rupturous_trail_remaining": sim.state.rupturous_trail_remaining,
        },
    }


def determinism_signature(sim: Simulation, steps: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "selected_action_sequence": [step["selected_action_id"] for step in steps],
        "resolved_action_sequence": [step["resolved_action_id"] for step in steps],
        "step_times": [
            {
                "step": step["step"],
                "combat_time_before": step["combat_time_before"],
                "combat_time_after": step["combat_time_after"],
                "current_time_before": step["current_time_before"],
                "current_time_after": step["current_time_after"],
            }
            for step in steps
        ],
        "scheduled_event_order": [
            {
                "event_type": event.get("event_type"),
                "combat_time": event.get("combat_time"),
                "scheduled_effect_id": event.get("scheduled_effect_id"),
                "payload_action_id": event.get("payload_action_id"),
                "source_action_id": event.get("source_action_id"),
                "host_action_id": event.get("host_action_id"),
            }
            for event in sim.state.scheduled_effect_event_log
        ],
        "final_state": sim.state.model_dump(mode="json"),
        "total_damage": sim.state.total_damage,
        "per_character_damage": _per_character_damage(sim),
    }


def assert_route_contract(run: FullCycleRun) -> None:
    result = run.result
    steps = result["steps"]
    assert result["selected_action_sequence"] == SELECTED_ROUTE
    assert result["resolved_action_sequence"] == EXPECTED_RESOLVED_ROUTE
    assert all(step["availability"] is True for step in steps)
    assert "short_wait" not in result["selected_action_sequence"]
    assert "short_wait" not in result["resolved_action_sequence"]
    fallback = result["placeholder_fallback"]
    assert fallback["count"] == 1
    assert fallback["locations"][0]["step"] == 6
    assert fallback["locations"][0]["selected_action_id"] == "swap_to_mornye"
    assert_close(result["totals"]["final_combat_time"], EXPECTED_FINAL_COMBAT_TIME, "final combat time")
    assert result["totals"]["final_combat_frames"] == EXPECTED_FINAL_COMBAT_FRAMES
    assert result["remaining_scheduled_effects"] == []
    assert result["party"]["build_profile_validation"]["ok"] is True

    by_step = {step["step"]: step for step in steps}
    assert_close(by_step[5]["off_tune"]["after"], 263.25, "after action 5 Off-Tune")
    assert by_step[6]["transition"]["transition_type"] == "normal_swap"
    assert by_step[6]["transition"]["fallback_swap_used"] is True
    assert by_step[6]["transition"]["swap_timing_is_placeholder"] is True
    assert_close(by_step[6]["action_time"], 0.5, "opening swap action time")
    assert_close(by_step[6]["combat_time_cost"], 0.5, "opening swap combat time")

    reactor = by_step[13]
    assert reactor["resolved_action_id"] == "mornye_echo_reactor_husk"
    assert_close(reactor["action_time"], 66 / 60, "Reactor Husk action time")
    assert_close(reactor["combat_time_cost"], 66 / 60, "Reactor Husk combat time")
    assert reactor["row"]["damage_bonus_category"] == "echo_ability"
    assert reactor["row"]["scaling_stat"] == "atk"
    assert_close(reactor["row"]["static_atk"], 1159.1645, "Reactor Husk static ATK", 1e-6)
    assert_close(reactor["row"]["final_atk_reference"], 1159.1645, "Reactor Husk final ATK reference", 1e-6)
    assert_close(reactor["row"]["runtime_atk_percent_bonus"], 0.25, "Reactor Husk runtime ATK buff", 1e-9)
    assert_close(reactor["row"]["scaling_value"], 1334.0395, "Reactor Husk buffed scaling value", 1e-6)
    assert reactor["damage"] > 0.0
    assert_close(reactor["row"]["base_resonance_energy_gain"], 4.87, "Reactor Husk base RE")
    assert_close(reactor["row"]["final_resonance_energy_gain"], 12.381488, "Reactor Husk final RE")
    assert_close(reactor["cooldowns"]["after"]["mornye_echo_reactor_husk"], 20.0, "Reactor Husk cooldown")
    assert reactor["off_tune"]["source_status"] == "unresolved_echo_off_tune"
    assert_close(reactor["off_tune"]["added"], 0.0, "Reactor Husk Off-Tune")

    assert_close(by_step[18]["off_tune"]["after"], 1926.27, "after Mornye step 18 Off-Tune")
    assert_close(by_step[18]["concerto_energy"]["after"]["mornye"], 100.0, "after Mornye step 18 Concerto")
    assert by_step[19]["resolved_action_id"] == "transition:lynae_intro_time_to_show_some_colors"
    assert by_step[19]["transition"]["outgoing_outro_event_id"] == "mornye_outro_recursion"
    assert by_step[19]["transition"]["incoming_intro_event_id"] == "lynae_intro_time_to_show_some_colors"
    assert by_step[19]["transition"]["fallback_swap_used"] is False
    assert by_step[19]["transition"]["swap_timing_is_placeholder"] is False
    assert_close(by_step[19]["concerto_energy"]["after"]["lynae"], 12.0, "Lynae after Intro Concerto")

    lynae_concerto = {
        19: 12.0,
        20: 21.83,
        21: 51.43,
        22: 56.83,
        23: 62.23,
        24: 65.73,
        25: 80.31,
        26: 100.0,
    }
    for step_index, expected in lynae_concerto.items():
        assert_close(
            by_step[step_index]["concerto_energy"]["after"]["lynae"],
            expected,
            f"Lynae Concerto after step {step_index}",
            1e-6,
        )
    assert_close(by_step[26]["concerto_energy"]["wasted_total_after"]["lynae"], 0.31, "Lynae wasted Concerto", 1e-6)
    lynae_off_tune = {
        19: 2085.87,
        20: 2216.70,
        21: 2611.20,
        22: 2683.20,
        23: 2755.20,
        24: 2801.70,
        25: 3716.10,
        26: 3920.00,
        27: 3920.00,
    }
    for step_index, expected in lynae_off_tune.items():
        assert_close(by_step[step_index]["off_tune"]["after"], expected, f"Off-Tune after step {step_index}", 1e-6)
    assert by_step[27]["off_tune"]["source_status"] == "unresolved_echo_off_tune"
    assert_close(by_step[27]["off_tune"]["added"], 0.0, "Hyvatia Off-Tune added")

    assert by_step[28]["resolved_action_id"] == "transition:aemeath_qte_intro_mech"
    assert by_step[28]["transition"]["outgoing_outro_event_id"] == "lynae_outro_lets_hit_the_road"
    assert by_step[28]["transition"]["incoming_intro_event_id"] == "aemeath_qte_intro_mech"
    assert by_step[28]["transition"]["fallback_swap_used"] is False
    assert by_step[28]["transition"]["swap_timing_is_placeholder"] is False
    assert_close(by_step[28]["concerto_energy"]["after"]["lynae"], 0.0, "Lynae Concerto after Aemeath transition")
    for buff_id in {
        "lynae_outro_all_damage_amp",
        "lynae_outro_liberation_damage_amp",
        "static_mist_incoming_atk",
        "pact_neonlight_incoming_atk",
    }:
        assert buff_id in by_step[28]["transition"]["applied_buffs"]

    tune_break = by_step[31]
    assert_close(tune_break["off_tune"]["before"], 3920.0, "Tune Break before Off-Tune")
    assert_close(tune_break["row"]["enemy_off_tune_current_before"], 3920.0, "Tune Break row before Off-Tune")
    assert_close(tune_break["row"]["enemy_off_tune_current_after_tune_break"], 0.0, "Tune Break after Off-Tune")
    assert_close(tune_break["tune_break"]["cooldown_after"], 3.0, "Tune Break cooldown")
    assert_close(tune_break["interfered_marker"]["remaining_after"], 8.0, "Interfered Marker after Tune Break")
    assert tune_break["row"]["party_response_scan_triggered"] is True
    assert len(tune_break["row"]["aemeath_rupturous_trail_gain_events"]) == 3
    assert tune_break["rupturous_trail"]["stacks_after"] == 30
    assert_close(tune_break["rupturous_trail"]["remaining_after"], 30.0, "Rupturous Trail after Tune Break")

    overdrive = by_step[32]
    assert_close(overdrive["combat_time_cost"], 0.0, "Overdrive combat time")
    assert_close(
        overdrive["rupturous_trail"]["remaining_after"],
        tune_break["rupturous_trail"]["remaining_after"],
        "Overdrive Rupturous Trail freeze",
    )
    assert_close(
        overdrive["interfered_marker"]["remaining_after"],
        tune_break["interfered_marker"]["remaining_after"],
        "Overdrive Interfered Marker freeze",
    )
    assert overdrive["row"]["mechanic_debug_after"]["aemeath"]["forte_enhancement_stacks"] == 2
    assert_close(overdrive["row"]["mechanic_debug_after"]["aemeath"]["forte_enhancement_remaining"], 30.0, "Overdrive forte duration")
    assert_close(overdrive["row"]["mechanic_debug_after"]["aemeath"]["trail_no_cost_remaining"], 30.0, "Overdrive Trail No-cost duration")

    sigillum = by_step[33]
    assert_close(sigillum["action_time"], 0.0, "Sigillum action time")
    assert_close(sigillum["combat_time_cost"], 0.0, "Sigillum combat time")
    assert_close(sigillum["damage"], 0.0, "Sigillum immediate damage")
    assert sigillum["row"]["aemeath_sigillum_activation_scheduled"] is True
    assert len(sigillum["row"]["aemeath_sigillum_hit_schedule_events"]) == 2

    first = by_step[37]
    assert first["row"]["aemeath_seraphic_duet_followup_variant"] == "enhanced"
    assert first["row"]["aemeath_seraphic_duet_followup_repeat_count"] == 10
    assert first["rupturous_trail"]["seraphic_snapshot"] == 30
    assert_close(first["rupturous_trail"]["seraphic_stack_factor"], 2.2, "first Seraphic Trail factor")
    assert_close(first["rupturous_trail"]["seraphic_total_extra_tune_multiplier"], 24.057, "first Seraphic extra tune", 1e-9)
    assert first["rupturous_trail"]["seraphic_preservation_active"] is True
    assert first["rupturous_trail"]["seraphic_consumed"] is False
    assert first["rupturous_trail"]["stacks_after"] == 30
    assert first["rupturous_trail"]["forte_stacks_before"] == 2
    assert first["rupturous_trail"]["forte_stacks_after"] == 1
    assert first["rupturous_trail"]["trail_no_cost_consumed"] is True

    second = by_step[41]
    assert second["row"]["aemeath_seraphic_duet_followup_variant"] == "enhanced"
    assert second["row"]["aemeath_seraphic_duet_followup_repeat_count"] == 10
    assert second["rupturous_trail"]["seraphic_snapshot"] == 30
    assert_close(second["rupturous_trail"]["seraphic_total_extra_tune_multiplier"], 24.057, "second Seraphic extra tune", 1e-9)
    assert second["rupturous_trail"]["seraphic_preservation_active"] is False
    assert second["rupturous_trail"]["seraphic_consumed"] is True
    assert second["rupturous_trail"]["stacks_after"] == 0
    assert_close(second["rupturous_trail"]["remaining_after"], 0.0, "second Seraphic Trail remaining")
    assert second["rupturous_trail"]["forte_stacks_before"] == 1
    assert second["rupturous_trail"]["forte_stacks_after"] == 0
    assert second["interfered_marker"]["remaining_before"] > 0.0
    assert_close(second["interfered_marker"]["remaining_after"], 7 / 60, "final Interfered Marker remaining", FRAME_TOLERANCE)


def assert_scheduled_event_contract(run: FullCycleRun) -> None:
    events = run.simulation.state.scheduled_effect_event_log
    by_step = {step["step"]: step for step in run.result["steps"]}
    visual_end = by_step[25]["combat_time_after"]
    sigillum_time = by_step[33]["combat_time_before"]

    high_heals = [
        event for event in events
        if event.get("event_type") == "scheduled_heal"
        and event.get("payload_action_id") == "mornye_high_syntony_field_heal"
    ]
    assert len(high_heals) >= 2
    high_heal_times = [event["combat_time"] for event in high_heals]
    for previous, current in zip(high_heal_times, high_heal_times[1:]):
        assert_close(current - previous, 3.0, "Mornye high Syntony heal spacing", 1e-9)
    assert {event.get("event_type") for event in high_heals} == {"scheduled_heal"}

    mornye_field_events = [
        event for event in events
        if event.get("source_action_id") == "mornye_heavy_geopotential_shift"
        and event.get("payload_action_id") in {
            "mornye_syntony_field_heal",
            "mornye_syntony_field_damage",
            "mornye_syntony_field_target_damage",
        }
    ]
    expected_field_events = [
        ("scheduled_heal", "mornye_syntony_field_heal", 7.8),
        ("scheduled_damage", "mornye_syntony_field_damage", 7.8),
        ("scheduled_damage", "mornye_syntony_field_target_damage", 8.166666666666666),
        ("scheduled_damage", "mornye_syntony_field_damage", 8.25),
    ]
    assert len(mornye_field_events) >= len(expected_field_events)
    for event, (event_type, payload_action_id, expected_time) in zip(
        mornye_field_events,
        expected_field_events,
        strict=False,
    ):
        assert event.get("event_type") == event_type
        assert event.get("payload_action_id") == payload_action_id
        assert_close(event.get("combat_time"), expected_time, f"{payload_action_id} timing", 1e-9)
    damage_field_events = mornye_field_events[1:4]
    assert [event.get("payload_action_id") for event in damage_field_events] == [
        "mornye_syntony_field_damage",
        "mornye_syntony_field_target_damage",
        "mornye_syntony_field_damage",
    ]
    for event in damage_field_events:
        assert event.get("source_character_id") == "mornye"
        assert float(event.get("damage", 0.0) or 0.0) > 0.0
    same_time_78 = [
        event.get("payload_action_id")
        for event in events
        if math.isclose(float(event.get("combat_time", -1.0)), 7.8, rel_tol=0.0, abs_tol=1e-9)
        and event.get("payload_action_id") in {"mornye_syntony_field_heal", "mornye_syntony_field_damage"}
    ]
    assert same_time_78[:2] == ["mornye_syntony_field_heal", "mornye_syntony_field_damage"]

    spray_events = [
        event for event in events
        if event.get("event_type") == "scheduled_status_application"
        and event.get("payload_action_id") == "lynae_spray_paint_flux_application"
    ]
    assert len(spray_events) == 3
    expected_spray_times = [visual_end + frames / FRAME_RATE for frames in (1, 121, 241)]
    for event, expected_time in zip(spray_events, expected_spray_times, strict=True):
        assert_close(event["combat_time"], expected_time, "Spray Paint status timing", 1e-9)
        assert_close(event.get("damage", 0.0), 0.0, "Spray Paint status damage")
        assert_close(event.get("off_tune_gain", 0.0), 0.0, "Spray Paint Off-Tune")
        assert_close(event.get("resonance_energy_gain", 0.0), 0.0, "Spray Paint RE")
        assert_close(event.get("concerto_energy_gain", 0.0), 0.0, "Spray Paint Concerto")

    sigillum_hits = [
        event for event in events
        if event.get("event_type") == "scheduled_damage"
        and event.get("source_action_id") == "aemeath_echo_sigillum"
    ]
    assert [event.get("payload_action_id") for event in sigillum_hits] == [
        "aemeath_echo_sigillum_hit_1",
        "aemeath_echo_sigillum_hit_2",
    ]
    expected_sigillum = [
        ("aemeath_echo_sigillum_hit_1", 25, 0.684, 0.23, 0.276),
        ("aemeath_echo_sigillum_hit_2", 55, 2.052, 2.13, 2.556),
    ]
    for event, (payload_id, frames, multiplier, base_re, final_re) in zip(sigillum_hits, expected_sigillum, strict=True):
        assert event.get("payload_action_id") == payload_id
        assert_close(event["combat_time"], sigillum_time + frames / FRAME_RATE, f"{payload_id} timing", 1e-9)
        assert event.get("damage_bonus_category") == "echo_ability"
        assert event.get("damage_element") == "fusion"
        assert event.get("scaling_stat") == "atk"
        hit_multiplier = event["hit_details"][0]["damage_multiplier"]
        assert_close(hit_multiplier, multiplier, f"{payload_id} multiplier")
        assert_close(event.get("base_resonance_energy_gain"), base_re, f"{payload_id} base RE")
        assert_close(event.get("final_resonance_energy_gain"), final_re, f"{payload_id} final RE", 1e-9)
    assert_close(sum(event.get("final_resonance_energy_gain", 0.0) or 0.0 for event in sigillum_hits), 2.832, "Sigillum total RE")

    overdrive = by_step[32]
    assert_close(overdrive["combat_time_before"], overdrive["combat_time_after"], "Overdrive combat-time freeze")
    overdrive_window_events = [
        event for event in events
        if overdrive["combat_time_before"] < event.get("combat_time", -1.0) <= overdrive["combat_time_after"]
    ]
    assert overdrive_window_events == []


def run_determinism_check() -> tuple[FullCycleRun, FullCycleRun]:
    first = execute_strict_route()
    second = execute_strict_route()
    assert_route_contract(first)
    assert_route_contract(second)
    assert_scheduled_event_contract(first)
    assert_scheduled_event_contract(second)
    if first.result["determinism_signature"] != second.result["determinism_signature"]:
        raise IntegrationFailure("full-cycle integration is not deterministic across two fresh Simulation instances")
    return first, second


def write_outputs(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "full_real_cycle_integration_v103_summary.json"
    timeline_path = output_dir / "full_real_cycle_integration_v103_timeline.csv"
    report_path = ROOT / "reports" / "full_real_cycle_integration_v103.md"

    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_timeline_csv(result, timeline_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(result), encoding="utf-8")


def _write_timeline_csv(result: dict[str, Any], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for step in result["steps"]:
        rows.append(
            {
                "timeline_sequence": 0,
                "timeline_sort_sequence": int(step["step"]),
                "policy_step": step["step"],
                "scheduled_event_sequence": "",
                "kind": "policy_action",
                "order": step["step"],
                "time": step["combat_time_before"],
                "end_time": step["combat_time_after"],
                "selected_action_id": step["selected_action_id"],
                "resolved_action_id": step["resolved_action_id"],
                "event_type": "",
                "payload_action_id": "",
                "source_action_id": "",
                "host_action_id": "",
                "damage": step["damage"],
                "off_tune_before": step["off_tune"]["before"],
                "off_tune_after": step["off_tune"]["after"],
                "notes": "",
            }
        )
    for order, event in enumerate(result["scheduled_effect_event_data"], start=1):
        rows.append(
            {
                "timeline_sequence": 0,
                "timeline_sort_sequence": int(order),
                "policy_step": "",
                "scheduled_event_sequence": order,
                "kind": event.get("event_type", "scheduled_event"),
                "order": order,
                "time": event.get("combat_time"),
                "end_time": event.get("combat_time"),
                "selected_action_id": "",
                "resolved_action_id": "",
                "event_type": event.get("event_type"),
                "payload_action_id": event.get("payload_action_id"),
                "source_action_id": event.get("source_action_id"),
                "host_action_id": event.get("host_action_id"),
                "damage": event.get("damage", 0.0),
                "off_tune_before": "",
                "off_tune_after": "",
                "notes": event.get("source_ref", ""),
            }
        )
    rows.sort(key=lambda row: (float(row["time"] or 0.0), int(row["timeline_sort_sequence"])))
    for timeline_sequence, row in enumerate(rows, start=1):
        row["timeline_sequence"] = timeline_sequence
    fieldnames = [
        "timeline_sequence",
        "timeline_sort_sequence",
        "policy_step",
        "scheduled_event_sequence",
        "kind",
        "order",
        "time",
        "end_time",
        "selected_action_id",
        "resolved_action_id",
        "event_type",
        "payload_action_id",
        "source_action_id",
        "host_action_id",
        "damage",
        "off_tune_before",
        "off_tune_after",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_report(result: dict[str, Any]) -> str:
    totals = result["totals"]
    fallback = result["placeholder_fallback"]
    damage_by_character = totals["damage_by_character"]
    lines = [
        "# Full Real-Cycle Integration Candidate 104",
        "",
        "This is a deterministic integration route through the verified active-Echo mechanics. It is not the 120-second manual baseline and is not claimed globally optimal.",
        "",
        f"- Baseline source: {BASELINE_ARCHIVE} / label {BASELINE_LABEL}",
        "- Candidate status: pending external review",
        f"- Final combat time: {totals['final_combat_time']}s / {totals['final_combat_frames']}F",
        f"- Total damage: {totals['total_damage']}",
        f"- Route-duration DPS: {totals['route_duration_dps_not_120_second_baseline']}",
        f"- Damage by character: {json.dumps(damage_by_character, ensure_ascii=False, sort_keys=True)}",
        f"- Placeholder/fallback swaps: {fallback['count']} at {json.dumps(fallback['locations'], ensure_ascii=False)}",
        "",
        "The opening Aemeath -> Mornye normal swap uses the known generic 0.50-second placeholder. Mornye -> Lynae and Lynae -> Aemeath use real enabled transition actions.",
        "",
        "## Major Checkpoints",
        "",
        f"- Aemeath opening Off-Tune after action 5: {result['checkpoint_values']['aemeath_opening']['after_step_5_enemy_off_tune']}",
        f"- Mornye Off-Tune after action 18: {result['checkpoint_values']['mornye_segment']['after_step_18_enemy_off_tune']}",
        f"- Mornye Concerto after action 18: {result['checkpoint_values']['mornye_segment']['after_step_18_mornye_concerto']}",
        f"- Tune Break Rupturous Trail stacks after action 31: {result['checkpoint_values']['tune_break']['rupturous_trail']['stacks_after']}",
        f"- First Seraphic Trail preserved: {result['checkpoint_values']['first_seraphic_duet']['rupturous_trail']['seraphic_preservation_active']}",
        f"- Second Seraphic Trail consumed: {result['checkpoint_values']['second_seraphic_duet']['rupturous_trail']['seraphic_consumed']}",
        f"- Final Interfered Marker remaining: {result['checkpoint_values']['final_state']['interfered_marker_remaining']}",
        "",
        "## Remaining Unresolved Limits",
        "",
    ]
    lines.extend(f"- {item}" for item in result["unresolved_limits"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-results", action="store_true")
    parser.add_argument("--output-dir", default=str(ROOT / "results"))
    args = parser.parse_args(argv)

    first, _second = run_determinism_check()
    if args.write_results:
        write_outputs(first.result, Path(args.output_dir))
    print(
        json.dumps(
            {
                "status": first.result["candidate"]["route_status"],
                "final_combat_time": first.result["totals"]["final_combat_time"],
                "final_combat_frames": first.result["totals"]["final_combat_frames"],
                "total_damage": first.result["totals"]["total_damage"],
                "route_duration_dps_not_120_second_baseline": first.result["totals"]["route_duration_dps_not_120_second_baseline"],
                "placeholder_fallback": first.result["placeholder_fallback"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
