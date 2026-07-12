from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.full_real_cycle_integration import (  # noqa: E402
    EXPECTED_RESOLVED_ROUTE,
    FLOAT_TOLERANCE,
    INITIAL_ACTIVE_CHARACTER,
    PARTY_ID,
    SELECTED_ROUTE,
    _build_step_record,
    _compact_event,
    _event_identity,
    _per_character_damage,
    _pre_resolved_id,
    _row_damage_attribution,
    _state_snapshot,
    assert_close,
    build_simulation,
)


SCHEMA_VERSION = "manual_120s_baseline_v1"
SOURCE_BASELINE_LABEL = "104"
CANDIDATE_LABEL = "105"
TARGET_COMBAT_TIME = 120.0
ROUTE_PATH = ROOT / "data" / "manual_120s_baseline_routes_v104.json"
SUMMARY_PATH = ROOT / "results" / "manual_120s_baseline_v104_summary.json"
TIMELINE_PATH = ROOT / "results" / "manual_120s_baseline_v104_timeline.csv"
REPORT_PATH = ROOT / "reports" / "manual_120s_baseline_v104.md"
COMPARISONS_PATH = ROOT / "results" / "manual_120s_baseline_v104_comparisons.json"
COMPARISONS_REPORT_PATH = ROOT / "reports" / "manual_120s_baseline_v104_comparisons.md"


class ManualBaselineFailure(AssertionError):
    pass


CHARACTER_IDS = ("aemeath", "mornye", "lynae")


PRIMARY_CONTINUATION = [
    "aemeath_basic_attack", "aemeath_basic_attack", "swap_to_mornye",
    "mornye_resonance_skill", "mornye_basic_attack", "mornye_basic_attack",
    "mornye_basic_attack", "mornye_heavy_attack", "mornye_basic_attack",
    "mornye_basic_attack", "mornye_resonance_liberation", "mornye_echo_reactor_husk",
    "swap_to_lynae", "lynae_resonance_skill", "lynae_spark_collision",
    "lynae_polychrome_leap", "lynae_polychrome_leap", "lynae_polychrome_leap",
    "lynae_visual_impact", "lynae_echo_hyvatia", "lynae_basic_attack",
    "lynae_basic_attack", "lynae_resonance_skill", "lynae_basic_attack",
    "swap_to_aemeath", "aemeath_tune_break", "aemeath_echo_sigillum",
    "aemeath_resonance_skill", "aemeath_basic_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_basic_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_basic_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_basic_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_basic_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_basic_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_basic_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_basic_attack", "aemeath_resonance_skill",
    "swap_to_mornye", "mornye_echo_reactor_husk", "mornye_resonance_skill",
    "mornye_basic_attack", "mornye_basic_attack", "mornye_basic_attack",
    "mornye_heavy_attack", "mornye_basic_attack", "mornye_basic_attack",
    "mornye_basic_attack", "swap_to_lynae", "lynae_echo_hyvatia",
    "lynae_resonance_skill", "lynae_resonance_liberation", "lynae_spark_collision",
    "lynae_polychrome_leap", "lynae_polychrome_leap", "lynae_polychrome_leap",
    "lynae_visual_impact", "swap_to_aemeath", "aemeath_tune_break",
    "aemeath_echo_sigillum", "aemeath_resonance_skill", "aemeath_basic_attack",
    "aemeath_resonance_skill", "aemeath_resonance_liberation",
    "aemeath_resonance_liberation", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "swap_to_mornye", "mornye_echo_reactor_husk", "mornye_resonance_skill",
    "mornye_resonance_liberation", "mornye_basic_attack", "mornye_basic_attack",
    "mornye_basic_attack", "swap_to_lynae", "lynae_echo_hyvatia",
    "lynae_resonance_skill", "lynae_spark_collision", "lynae_polychrome_leap",
    "lynae_polychrome_leap", "lynae_polychrome_leap", "lynae_visual_impact",
    "lynae_basic_attack", "lynae_basic_attack", "lynae_basic_attack",
]


NO_LYNAE_ROUTE = [
    "aemeath_resonance_liberation", "aemeath_echo_sigillum", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_echo_sigillum",
    "aemeath_resonance_skill", "aemeath_heavy_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "swap_to_mornye", "mornye_resonance_liberation",
    "mornye_echo_reactor_husk", "mornye_resonance_skill", "mornye_basic_attack",
    "mornye_basic_attack", "mornye_basic_attack", "swap_to_aemeath",
    "aemeath_resonance_skill", "aemeath_heavy_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_heavy_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_heavy_attack", "aemeath_resonance_skill",
    "aemeath_tune_break", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_echo_sigillum", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "swap_to_mornye",
    "mornye_echo_reactor_husk", "mornye_resonance_skill", "mornye_heavy_attack",
    "mornye_basic_attack", "mornye_basic_attack", "mornye_basic_attack",
    "mornye_basic_attack", "mornye_resonance_liberation", "swap_to_aemeath",
    "aemeath_resonance_liberation", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_echo_sigillum", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_tune_break",
    "aemeath_resonance_skill", "aemeath_heavy_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_heavy_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_heavy_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "aemeath_heavy_attack", "aemeath_resonance_skill",
    "aemeath_resonance_skill", "swap_to_mornye", "mornye_echo_reactor_husk",
    "mornye_resonance_skill", "mornye_heavy_attack", "mornye_basic_attack",
    "mornye_basic_attack", "mornye_basic_attack", "mornye_basic_attack",
    "mornye_basic_attack", "mornye_basic_attack", "swap_to_aemeath",
    "aemeath_echo_sigillum", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_echo_sigillum", "swap_to_mornye",
    "mornye_echo_reactor_husk", "mornye_resonance_skill", "mornye_resonance_liberation",
    "mornye_basic_attack", "mornye_basic_attack", "mornye_basic_attack",
    "swap_to_aemeath", "aemeath_tune_break", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill",
]


REACTOR_VARIANT_ROUTE = [
    "aemeath_basic_attack", "aemeath_basic_attack", "aemeath_basic_attack",
    "aemeath_basic_attack", "aemeath_resonance_skill", "swap_to_mornye",
    "mornye_echo_reactor_husk", "mornye_resonance_liberation", "mornye_resonance_skill",
    "mornye_heavy_attack", "mornye_heavy_attack", "mornye_heavy_attack",
    "mornye_heavy_attack", "mornye_resonance_skill", "mornye_heavy_attack",
    "mornye_heavy_attack", "mornye_resonance_skill", "mornye_basic_attack",
    "mornye_basic_attack", "mornye_basic_attack", "mornye_heavy_attack",
    "swap_to_lynae", "lynae_echo_hyvatia", "lynae_resonance_skill",
    "lynae_resonance_liberation", "lynae_spark_collision", "lynae_polychrome_leap",
    "lynae_polychrome_leap", "lynae_polychrome_leap", "lynae_visual_impact",
    "swap_to_aemeath", "aemeath_tune_break", "aemeath_echo_sigillum",
    "aemeath_resonance_liberation", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "swap_to_mornye", "mornye_echo_reactor_husk", "mornye_resonance_skill",
    "mornye_basic_attack", "mornye_basic_attack", "mornye_basic_attack",
    "mornye_resonance_liberation", "swap_to_lynae", "lynae_echo_hyvatia",
    "lynae_resonance_skill", "lynae_spark_collision", "lynae_polychrome_leap",
    "lynae_polychrome_leap", "lynae_polychrome_leap", "lynae_visual_impact",
    "lynae_basic_attack", "lynae_basic_attack", "lynae_basic_attack",
    "lynae_resonance_skill", "swap_to_aemeath", "aemeath_tune_break",
    "aemeath_echo_sigillum", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_resonance_skill", "aemeath_heavy_attack",
    "aemeath_resonance_skill", "aemeath_echo_sigillum", "swap_to_mornye",
    "mornye_echo_reactor_husk", "mornye_resonance_skill", "mornye_basic_attack",
    "mornye_basic_attack", "mornye_basic_attack", "mornye_heavy_attack",
    "mornye_basic_attack", "mornye_basic_attack", "mornye_basic_attack",
    "swap_to_lynae", "lynae_echo_hyvatia", "lynae_resonance_skill",
    "lynae_resonance_liberation", "lynae_spark_collision", "lynae_polychrome_leap",
    "lynae_polychrome_leap", "lynae_polychrome_leap", "lynae_visual_impact",
    "swap_to_aemeath", "aemeath_tune_break", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_liberation", "aemeath_heavy_attack",
    "aemeath_echo_sigillum", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_skill",
    "aemeath_heavy_attack", "aemeath_resonance_skill",
]


ROUTE_DEFINITIONS = {
    "primary": {
        "selected": SELECTED_ROUTE + PRIMARY_CONTINUATION,
        "notes": "Full party deterministic manual baseline. First 41 actions are candidate-104 verified route.",
    },
    "no_lynae_control": {
        "selected": NO_LYNAE_ROUTE,
        "notes": "Comparison control; same party preset but no Lynae selected policy actions.",
    },
    "reactor_husk_order_variant": {
        "selected": REACTOR_VARIANT_ROUTE,
        "notes": "Comparison control; Reactor Husk is placed at the first legal pre-Liberation Mornye position when legal.",
    },
}


def _sequence_hash(sequence: list[str]) -> str:
    payload = json.dumps(sequence, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_routes_or_defaults() -> dict[str, Any]:
    if ROUTE_PATH.exists():
        return json.loads(ROUTE_PATH.read_text(encoding="utf-8-sig"))
    return _build_route_payload()


def _route_stage_boundaries(name: str, selected: list[str]) -> list[dict[str, Any]]:
    if name == "primary":
        return [
            {
                "stage": "verified_candidate_104_opening",
                "start_step": 1,
                "end_step": 41,
                "reason": "Byte-for-byte candidate-104 verified selected/resolved route.",
            },
            {
                "stage": "aemeath_concerto_bridge_to_mornye",
                "start_step": 42,
                "end_step": 44,
                "reason": "Two Aemeath basics naturally finish Concerto for a real Mornye Intro transition.",
            },
            {
                "stage": "mornye_post_liberation_support",
                "start_step": 45,
                "end_step": 54,
                "reason": "Mornye builds field/support resources, uses Liberation then Reactor Husk, and exits with real Concerto.",
            },
            {
                "stage": "lynae_core_without_second_liberation",
                "start_step": 55,
                "end_step": 66,
                "reason": "Lynae spends available verified core actions and filler basics until natural Aemeath transition.",
            },
            {
                "stage": "aemeath_tune_break_and_concerto_rebuild",
                "start_step": 67,
                "end_step": 93,
                "reason": "Aemeath uses available Tune Break/Sigillum and legal skill/basic filler to rebuild Concerto.",
            },
            {
                "stage": "second_mornye_to_lynae_cycle",
                "start_step": 94,
                "end_step": 112,
                "reason": "Mornye and Lynae continue fixed role order with legal Echo/Liberation/core actions.",
            },
            {
                "stage": "aemeath_second_tune_break_and_overdrive_window",
                "start_step": 113,
                "end_step": 131,
                "reason": "Aemeath consumes Tune Break and available Overdrive/Finale while naturally rebuilding Concerto.",
            },
            {
                "stage": "final_mornye_lynae_cutoff_segment",
                "start_step": 132,
                "end_step": 148,
                "reason": "Final Mornye support and Lynae core actions run until existing combat-time cutoff clips the last basic.",
            },
        ]
    boundaries = [
        {
            "stage": "opening_verified_104",
            "start_step": 1,
            "end_step": min(41, len(selected)),
            "reason": "Candidate-104 verified full real-cycle opening reused byte-for-byte where applicable.",
        }
    ] if name == "primary" else []
    chunks = [
        ("manual_continuation", 42 if name == "primary" else 1, len(selected), ROUTE_DEFINITIONS[name]["notes"]),
    ]
    for stage, start, end, reason in chunks:
        if start <= end:
            boundaries.append({"stage": stage, "start_step": start, "end_step": end, "reason": reason})
    return boundaries


def _execute_selected(selected: list[str], expected_resolved: list[str] | None = None) -> dict[str, Any]:
    if "short_wait" in selected:
        raise ManualBaselineFailure("short_wait is forbidden in manual baseline routes")
    sim = build_simulation()
    steps: list[dict[str, Any]] = []
    resolved: list[str] = []
    for index, selected_action_id in enumerate(selected, start=1):
        if sim.state.combat_time >= TARGET_COMBAT_TIME:
            raise ManualBaselineFailure(f"route contains action after cutoff at step {index}: {selected_action_id}")
        if selected_action_id not in sim.policy_actions:
            raise ManualBaselineFailure(f"step {index}: {selected_action_id} is not a policy action")
        selected_action = sim.policy_actions[selected_action_id]
        pre_resolved_action_id = _pre_resolved_id(sim, selected_action_id)
        if not sim.is_action_available(selected_action):
            raise ManualBaselineFailure(
                json.dumps(
                    {
                        "reason": "selected policy action unavailable",
                        "step": index,
                        "selected_action_id": selected_action_id,
                        "pre_resolved_action_id": pre_resolved_action_id,
                        "combat_time": sim.state.combat_time,
                        "active_character_id": sim.state.active_character_id,
                        "valid_policy_actions": sim.valid_action_ids(),
                        "resonance_energy": dict(sim.state.resonance_energy),
                        "concerto_energy": dict(sim.state.concerto_energy),
                        "cooldowns": dict(sim.state.cooldowns),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        before = _state_snapshot(sim)
        ok = sim.execute_action(selected_action_id)
        if not ok or not sim.timeline:
            raise ManualBaselineFailure(f"step {index}: execute_action failed for {selected_action_id}")
        row = sim.timeline[-1]
        after = _state_snapshot(sim)
        expected = expected_resolved[index - 1] if expected_resolved else row.resolved_action_id
        if row.selected_action_id != selected_action_id:
            raise ManualBaselineFailure(f"step {index}: selected action was replaced by {row.selected_action_id}")
        if row.resolved_action_id != expected:
            raise ManualBaselineFailure(
                f"step {index}: expected resolved {expected}, got {row.resolved_action_id}"
            )
        resolved.append(row.resolved_action_id)
        steps.append(
            _build_step_record(
                step_index=index,
                selected_action_id=selected_action_id,
                expected_resolved_action_id=expected,
                pre_resolved_action_id=pre_resolved_action_id,
                before=before,
                after=after,
                row=row,
            )
        )
    assert_close(sim.state.combat_time, TARGET_COMBAT_TIME, "manual baseline final combat_time", 1e-9)
    return {"simulation": sim, "steps": steps, "resolved": resolved}


def _build_route_payload() -> dict[str, Any]:
    routes: dict[str, Any] = {}
    for name, definition in ROUTE_DEFINITIONS.items():
        selected = list(definition["selected"])
        resolved = _execute_selected(selected)["resolved"]
        routes[name] = {
            "route_name": name,
            "human_authored": True,
            "global_optimum_claimed": False,
            "selected_policy_actions": selected,
            "expected_resolved_actions": resolved,
            "selected_sequence_sha256": _sequence_hash(selected),
            "resolved_sequence_sha256": _sequence_hash(resolved),
            "stage_boundaries": _route_stage_boundaries(name, selected),
            "notes": definition["notes"],
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "source_baseline_label": SOURCE_BASELINE_LABEL,
        "candidate_label": CANDIDATE_LABEL,
        "party_id": PARTY_ID,
        "initial_active_character": INITIAL_ACTIVE_CHARACTER,
        "statement": "Human-authored deterministic references; not globally optimal.",
        "routes": routes,
    }


def _complete_event_record(event: dict[str, Any]) -> dict[str, Any]:
    compact = _compact_event(event)
    for key in (
        "resource_recipient_character_id",
        "resonance_energy_gained",
        "resonance_energy_wasted",
        "concerto_energy_gained",
        "concerto_energy_wasted",
    ):
        if key in event:
            compact[key] = event.get(key)
    return compact


def _resource_actor(row: Any) -> str:
    return str(row.actor_character_id or row.character_id or row.active_character_before or "unknown")


def _resource_event_recipient(event: dict[str, Any]) -> str:
    return str(event.get("resource_recipient_character_id") or event.get("source_character_id") or "unknown")


def _source_aware_resource_summary(sim: Any, steps: list[dict[str, Any]], resource_name: str) -> dict[str, Any]:
    if resource_name not in {"resonance_energy", "concerto_energy"}:
        raise ManualBaselineFailure(f"Unsupported resource summary: {resource_name}")
    gained_field = f"{resource_name}_gained"
    wasted_field = f"{resource_name}_wasted"

    initial = {
        char: float(steps[0][resource_name]["before"].get(char, 0.0) or 0.0)
        for char in CHARACTER_IDS
    }
    final = {
        char: float(getattr(sim.state, resource_name).get(char, 0.0) or 0.0)
        for char in CHARACTER_IDS
    }

    direct_gained = defaultdict(float)
    direct_wasted = defaultdict(float)
    direct_events: list[dict[str, Any]] = []
    for index, row in enumerate(sim.timeline, start=1):
        recipient = _resource_actor(row)
        gained = float(getattr(row, gained_field, 0.0) or 0.0)
        wasted = float(getattr(row, wasted_field, 0.0) or 0.0)
        direct_gained[recipient] += gained
        direct_wasted[recipient] += wasted
        if gained or wasted:
            direct_events.append(
                {
                    "step": index,
                    "selected_action_id": row.selected_action_id,
                    "resolved_action_id": row.resolved_action_id,
                    "recipient": recipient,
                    "gained": gained,
                    "wasted": wasted,
                }
            )

    scheduled_gained = defaultdict(float)
    scheduled_wasted = defaultdict(float)
    scheduled_events: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for event in sim.state.scheduled_effect_event_log:
        key = _event_identity("scheduled_effect_event_log", event)
        if key in seen:
            continue
        seen.add(key)
        gained = float(event.get(gained_field, 0.0) or 0.0)
        wasted = float(event.get(wasted_field, 0.0) or 0.0)
        if not gained and not wasted:
            continue
        recipient = _resource_event_recipient(event)
        scheduled_gained[recipient] += gained
        scheduled_wasted[recipient] += wasted
        scheduled_events.append(
            {
                "event_identity": list(key),
                "combat_time": event.get("combat_time"),
                "event_type": event.get("event_type"),
                "payload_action_id": event.get("payload_action_id"),
                "source_action_id": event.get("source_action_id"),
                "source_character_id": event.get("source_character_id"),
                "resource_recipient_character_id": event.get("resource_recipient_character_id"),
                "recipient": recipient,
                "gained": gained,
                "wasted": wasted,
            }
        )

    gained = {
        char: float(direct_gained[char] + scheduled_gained[char])
        for char in CHARACTER_IDS
    }
    wasted = {
        char: float(direct_wasted[char] + scheduled_wasted[char])
        for char in CHARACTER_IDS
    }
    spent: dict[str, float] = {}
    conservation: dict[str, dict[str, float]] = {}
    for char in CHARACTER_IDS:
        value = initial[char] + gained[char] - final[char]
        if value < 0 and abs(value) <= FLOAT_TOLERANCE:
            value = 0.0
        spent[char] = value
        conservation[char] = {
            "initial_plus_gained_minus_spent": initial[char] + gained[char] - spent[char],
            "final": final[char],
            "delta": initial[char] + gained[char] - spent[char] - final[char],
        }

    state_wasted = getattr(
        sim.state,
        "wasted_resonance_energy" if resource_name == "resonance_energy" else "wasted_concerto_energy",
    )
    for char in CHARACTER_IDS:
        assert_close(wasted[char], float(state_wasted.get(char, 0.0) or 0.0), f"{resource_name} wasted {char}", 1e-9)
        assert_close(conservation[char]["delta"], 0.0, f"{resource_name} conservation {char}", 1e-9)

    return {
        "initial": dict(sorted(initial.items())),
        "gained": dict(sorted(gained.items())),
        "spent": dict(sorted(spent.items())),
        "wasted": dict(sorted(wasted.items())),
        "final": dict(sorted(final.items())),
        "direct": {
            "gained": dict(sorted((char, direct_gained[char]) for char in CHARACTER_IDS)),
            "wasted": dict(sorted((char, direct_wasted[char]) for char in CHARACTER_IDS)),
            "events": direct_events,
        },
        "scheduled": {
            "gained": dict(sorted((char, scheduled_gained[char]) for char in CHARACTER_IDS)),
            "wasted": dict(sorted((char, scheduled_wasted[char]) for char in CHARACTER_IDS)),
            "events": scheduled_events,
        },
        "conservation": conservation,
    }


def _complete_damage_by_bonus_category(sim: Any, total_damage: float) -> dict[str, float]:
    categories = {
        key: float(value)
        for key, value in sim.summary().damage_by_damage_bonus_category.items()
    }
    assert_close(sum(categories.values()), total_damage, "damage category sum", 1e-6)
    return dict(sorted(categories.items()))


def _active_echo_summary(sim: Any) -> dict[str, Any]:
    echo_action_ids = {
        "mornye_echo_reactor_husk",
        "lynae_echo_hyvatia",
        "aemeath_echo_sigillum",
    }
    summary: dict[str, dict[str, Any]] = {
        action_id: {
            "activation_count": 0,
            "direct_damage": 0.0,
            "scheduled_damage": 0.0,
            "total_damage": 0.0,
            "resolved_hit_count": 0,
            "excluded_after_cutoff_hit_count": 0,
            "excluded_after_cutoff_damage": 0.0,
            "excluded_after_cutoff_resonance_energy": 0.0,
        }
        for action_id in sorted(echo_action_ids)
    }
    for row in sim.timeline:
        if row.selected_action_id not in echo_action_ids:
            continue
        item = summary[row.selected_action_id]
        item["activation_count"] += 1
        item["direct_damage"] += float(row.direct_action_damage or 0.0)
        item["resolved_hit_count"] += int(getattr(row, "hit_count", 0) or 0)
        item["excluded_after_cutoff_damage"] += float(row.damage_after_cutoff_excluded or 0.0)
        if row.truncated_by_combat_limit and float(row.damage_after_cutoff_excluded or 0.0) > 0.0:
            item["excluded_after_cutoff_hit_count"] += 1

    seen: set[tuple[Any, ...]] = set()
    for event in sim.state.scheduled_effect_event_log:
        source_action_id = event.get("source_action_id")
        if source_action_id not in echo_action_ids:
            continue
        key = _event_identity("scheduled_effect_event_log", event)
        if key in seen:
            continue
        seen.add(key)
        item = summary[source_action_id]
        damage = float(event.get("damage", 0.0) or 0.0)
        item["scheduled_damage"] += damage
        if damage:
            item["resolved_hit_count"] += 1

    for effect in sim.state.scheduled_effects:
        data = effect.model_dump(mode="json") if hasattr(effect, "model_dump") else dict(effect)
        source_action_id = data.get("source_action_id")
        if source_action_id not in echo_action_ids:
            continue
        next_time = data.get("next_trigger_time")
        if next_time is None or float(next_time) <= TARGET_COMBAT_TIME:
            continue
        item = summary[source_action_id]
        item["excluded_after_cutoff_hit_count"] += 1
        payload = data.get("payload", {}) if isinstance(data.get("payload"), dict) else {}
        item["excluded_after_cutoff_damage"] += float(payload.get("damage", 0.0) or 0.0)
        item["excluded_after_cutoff_resonance_energy"] += float(payload.get("resonance_energy_gain", 0.0) or 0.0)

    for item in summary.values():
        item["total_damage"] = item["direct_damage"] + item["scheduled_damage"]
    summary["total_active_echo_damage"] = sum(
        item["total_damage"]
        for key, item in summary.items()
        if isinstance(item, dict)
    )
    return summary


def _count_windows(events: list[dict[str, Any]]) -> dict[str, Any]:
    times = [event.get("combat_time") for event in events if event.get("combat_time") is not None]
    return {
        "event_count": len(events),
        "first_time": min(times) if times else None,
        "last_time": max(times) if times else None,
    }


def _summarize_run(name: str, selected: list[str], resolved: list[str], sim: Any, steps: list[dict[str, Any]]) -> dict[str, Any]:
    total_damage = sum(float(row.damage or 0.0) for row in sim.timeline)
    simulation_summary = sim.summary().model_dump(mode="json")
    damage_by_character = _per_character_damage(sim)
    assert_close(sum(damage_by_character.values()), total_damage, f"{name} damage attribution sum", 1e-6)
    damage_by_selected = defaultdict(float)
    damage_by_resolved = defaultdict(float)
    damage_by_action_type = defaultdict(float)
    for row in sim.timeline:
        damage_by_selected[row.selected_action_id] += float(row.damage or 0.0)
        damage_by_resolved[row.resolved_action_id] += float(row.damage or 0.0)
        action = sim.actions.get(row.resolved_action_id)
        damage_by_action_type[getattr(action, "action_type", "unknown")] += float(row.damage or 0.0)
    swaps = [
        {
            "step": step["step"],
            "selected_action_id": step["selected_action_id"],
            "resolved_action_id": step["resolved_action_id"],
            "combat_time_before": step["combat_time_before"],
            "combat_time_after": step["combat_time_after"],
            **step["transition"],
        }
        for step in steps
        if step["selected_action_id"].startswith("swap_to_")
    ]
    placeholder_steps = [
        swap for swap in swaps
        if swap.get("fallback_swap_used") or swap.get("swap_timing_is_placeholder")
    ]
    tune_breaks = [
        {
            "step": step["step"],
            "selected_action_id": step["selected_action_id"],
            "resolved_action_id": step["resolved_action_id"],
            "combat_time": step["combat_time_before"],
            "response_damage": sum(float(event.get("damage", 0.0) or 0.0) for event in step["tune_break"]["tune_response_events"]),
            "response_events": step["tune_break"]["tune_response_events"],
            "lockout_window": [step["combat_time_before"], step["combat_time_before"] + 3.0],
        }
        for step in steps
        if step["resolved_action_id"].endswith("tune_break")
    ]
    final_row = sim.timeline[-1]
    scheduled_events = [_complete_event_record(event) for event in sim.state.scheduled_effect_event_log]
    active_echo_summary = _active_echo_summary(sim)
    sigillum_scheduled_hits = [
        event for event in scheduled_events
        if event.get("source_action_id") == "aemeath_echo_sigillum"
    ]
    sigillum_excluded = active_echo_summary["aemeath_echo_sigillum"]
    mornye_field_events = [
        event for event in scheduled_events
        if str(event.get("payload_action_id", "")).startswith(("mornye_syntony", "mornye_high_syntony"))
    ]
    lynae_spray_events = [
        event for event in scheduled_events
        if event.get("payload_action_id") == "lynae_spray_paint_flux_application"
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_name": name,
        "source_baseline_label": SOURCE_BASELINE_LABEL,
        "candidate_label": CANDIDATE_LABEL,
        "external_review_status": "pending",
        "party": {
            "party_id": PARTY_ID,
            "initial_active_character": INITIAL_ACTIVE_CHARACTER,
            "build_profile_validation": getattr(sim, "build_profile_validation", {"ok": True}),
        },
        "observation": {"version": "slot_generic_mechanics_v5", "shape": 314},
        "policy": {"action_count": len(sim.get_policy_action_ids()), "ordered_policy_ids": sim.get_policy_action_ids()},
        "total_damage": total_damage,
        "dps": total_damage / TARGET_COMBAT_TIME,
        "final_combat_time": sim.state.combat_time,
        "final_current_time": sim.state.current_time,
        "selected_action_sequence": selected,
        "resolved_action_sequence": resolved,
        "selected_action_count": len(selected),
        "resolved_action_count": len(resolved),
        "selected_sequence_sha256": _sequence_hash(selected),
        "resolved_sequence_sha256": _sequence_hash(resolved),
        "damage_by_character": damage_by_character,
        "damage_by_selected_action": dict(sorted(damage_by_selected.items())),
        "damage_by_resolved_action": dict(sorted(damage_by_resolved.items())),
        "damage_by_action_type": dict(sorted(damage_by_action_type.items())),
        "damage_by_damage_bonus_category": _complete_damage_by_bonus_category(sim, total_damage),
        "selected_action_counts": dict(Counter(selected)),
        "resolved_action_counts": dict(Counter(resolved)),
        "resonance_energy": _source_aware_resource_summary(sim, steps, "resonance_energy"),
        "concerto_energy": _source_aware_resource_summary(sim, steps, "concerto_energy"),
        "swaps": swaps,
        "placeholder_fallback": {"count": len(placeholder_steps), "steps": placeholder_steps},
        "off_tune_timeline": [
            {"step": step["step"], "before": step["off_tune"]["before"], "after": step["off_tune"]["after"]}
            for step in steps
        ],
        "tune_breaks": tune_breaks,
        "rupturous_trail_timeline": [step["rupturous_trail"] | {"step": step["step"]} for step in steps],
        "interfered_marker_windows": [
            {
                "step": step["step"],
                "remaining_before": step["interfered_marker"]["remaining_before"],
                "remaining_after": step["interfered_marker"]["remaining_after"],
                "newly_applied_this_action": step["interfered_marker"]["newly_applied_this_action"],
            }
            for step in steps
        ],
        "mornye_field_events": mornye_field_events,
        "mornye_field_summary": _count_windows(mornye_field_events),
        "lynae_spray_paint_events": lynae_spray_events,
        "lynae_spray_paint_summary": _count_windows(lynae_spray_events),
        "aemeath_sigillum": {
            "activations": [
                step for step in steps
                if step["selected_action_id"] == "aemeath_echo_sigillum"
            ],
            "scheduled_hits": sigillum_scheduled_hits,
            "resolved_hit_count": sigillum_excluded["resolved_hit_count"],
            "excluded_after_cutoff_hit_count": sigillum_excluded["excluded_after_cutoff_hit_count"],
            "excluded_after_cutoff_damage": sigillum_excluded["excluded_after_cutoff_damage"],
            "excluded_after_cutoff_resonance_energy": sigillum_excluded["excluded_after_cutoff_resonance_energy"],
        },
        "active_echo_usage_counts": dict(Counter(action for action in selected if "_echo_" in action)),
        "active_echo_summary": active_echo_summary,
        "uptime_summary": {
            "everbright_polestar_liberation_penetration_uptime_seconds": simulation_summary.get("everbright_polestar_liberation_penetration_uptime_seconds"),
            "aemeath_trailblazing_star_5set_uptime_seconds": simulation_summary.get("aemeath_trailblazing_star_5set_uptime_seconds"),
            "mornye_halo_of_starry_radiance_5set_uptime_seconds": simulation_summary.get("mornye_halo_of_starry_radiance_5set_uptime_seconds"),
        },
        "simulation_summary": simulation_summary,
        "remaining_scheduled_effects_at_cutoff": [
            effect.model_dump(mode="json") if hasattr(effect, "model_dump") else dict(effect)
            for effect in sim.state.scheduled_effects
        ],
        "scheduled_effect_event_data": scheduled_events,
        "final_clipped_action": {
            "step": len(steps),
            "selected_action_id": final_row.selected_action_id,
            "resolved_action_id": final_row.resolved_action_id,
            "start_time": final_row.combat_time_start,
            "end_time": final_row.combat_time_end,
            "full_combat_time_cost": final_row.combat_time_cost,
            "effective_clipped_cost": final_row.effective_combat_time_cost,
            "truncated_by_combat_limit": final_row.truncated_by_combat_limit,
            "damage_before_cutoff": final_row.damage_before_cutoff,
            "damage_after_cutoff_excluded": final_row.damage_after_cutoff_excluded,
        },
        "known_limitations": [
            "Opening normal-swap exact timing placeholder remains unresolved.",
            "Mornye exact dodge-cancel next-input frame remains unresolved.",
            "Source-unconfirmed active-Echo Off-Tune values remain runtime zero where unresolved.",
            "Lynae Hyvatia Off-Tune source uncertainty remains unresolved.",
        ],
        "steps": steps,
    }


def execute_route(name: str = "primary", *, routes_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    routes_payload = routes_payload or _load_routes_or_defaults()
    route = routes_payload["routes"][name]
    selected = list(route["selected_policy_actions"])
    expected = list(route["expected_resolved_actions"])
    run = _execute_selected(selected, expected)
    result = _summarize_run(name, selected, run["resolved"], run["simulation"], run["steps"])
    if result["selected_sequence_sha256"] != route["selected_sequence_sha256"]:
        raise ManualBaselineFailure(f"{name} selected route hash mismatch")
    if result["resolved_sequence_sha256"] != route["resolved_sequence_sha256"]:
        raise ManualBaselineFailure(f"{name} resolved route hash mismatch")
    return result


def run_all() -> dict[str, Any]:
    routes = _load_routes_or_defaults()
    return {name: execute_route(name, routes_payload=routes) for name in routes["routes"]}


def _write_route_file() -> dict[str, Any]:
    payload = _build_route_payload()
    ROUTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROUTE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _write_timeline_csv(result: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for step in result["steps"]:
        attribution = _row_damage_attribution(type("RowProxy", (), step["row"])())
        rows.append(
            {
                "timeline_sequence": 0,
                "timeline_sort_sequence": step["step"] * 100000,
                "policy_step": step["step"],
                "scheduled_event_sequence": "",
                "kind": "policy_action",
                "time": step["combat_time_before"],
                "end_time": step["combat_time_after"],
                "selected_action_id": step["selected_action_id"],
                "resolved_action_id": step["resolved_action_id"],
                "event_type": "",
                "payload_action_id": "",
                "source_action_id": "",
                "source_character_id": attribution["actor_character_id"],
                "damage": step["damage"],
                "damage_attribution": json.dumps(attribution["damage_by_character"], sort_keys=True),
            }
        )
    for order, event in enumerate(result["scheduled_effect_event_data"], start=1):
        rows.append(
            {
                "timeline_sequence": 0,
                "timeline_sort_sequence": order,
                "policy_step": "",
                "scheduled_event_sequence": order,
                "kind": event.get("event_type", "scheduled_event"),
                "time": event.get("combat_time"),
                "end_time": event.get("combat_time"),
                "selected_action_id": "",
                "resolved_action_id": "",
                "event_type": event.get("event_type"),
                "payload_action_id": event.get("payload_action_id"),
                "source_action_id": event.get("source_action_id"),
                "source_character_id": event.get("source_character_id"),
                "damage": event.get("damage", 0.0),
                "damage_attribution": json.dumps(
                    {event.get("source_character_id"): event.get("damage", 0.0)}
                    if event.get("source_character_id") and event.get("damage") else {},
                    sort_keys=True,
                ),
            }
        )
    rows.sort(key=lambda row: (float(row["time"] or 0.0), int(row["timeline_sort_sequence"])))
    for sequence, row in enumerate(rows, start=1):
        row["timeline_sequence"] = sequence
    TIMELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TIMELINE_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _render_report(primary: dict[str, Any]) -> str:
    damage = primary["damage_by_character"]
    total = primary["total_damage"]
    resonance = primary["resonance_energy"]
    concerto = primary["concerto_energy"]
    categories = primary["damage_by_damage_bonus_category"]
    echo_summary = primary["active_echo_summary"]
    uptime = primary["uptime_summary"]
    lines = [
        "# Manual 120-Second Baseline Candidate 105",
        "",
        "This is a deterministic human-authored 120.0 combat-second baseline for comparison. It is not a global optimum.",
        "",
        f"- Source baseline: 104 / ww-dps-simulator-2(104).zip",
        "- Candidate status: pending external review",
        f"- Total damage: {total}",
        f"- DPS: {primary['dps']}",
        f"- Final combat time: {primary['final_combat_time']}",
        f"- Final current/action time: {primary['final_current_time']}",
        f"- Selected/resolved actions: {primary['selected_action_count']} / {primary['resolved_action_count']}",
        f"- Selected hash: `{primary['selected_sequence_sha256']}`",
        f"- Resolved hash: `{primary['resolved_sequence_sha256']}`",
        f"- Damage by character: {json.dumps(damage, ensure_ascii=False, sort_keys=True)}",
        f"- Placeholder swaps: {primary['placeholder_fallback']['count']} at {[item['step'] for item in primary['placeholder_fallback']['steps']]}",
        f"- Tune Break times: {[item['combat_time'] for item in primary['tune_breaks']]}",
        f"- Final clipped action: {json.dumps(primary['final_clipped_action'], ensure_ascii=False, sort_keys=True)}",
        "",
        "## Contribution",
        "",
    ]
    for character, value in damage.items():
        lines.append(f"- {character}: {value} ({value / total * 100.0:.4f}%)")
    lines.extend(
        [
            "",
            "## Action Counts",
            "",
        ]
    )
    for action_id, count in sorted(primary["selected_action_counts"].items()):
        lines.append(f"- {action_id}: {count}")
    lines.extend(
        [
            "",
            "## Resources",
            "",
            f"- Resonance Energy initial: {json.dumps(resonance['initial'], sort_keys=True)}",
            f"- Resonance Energy gained: {json.dumps(resonance['gained'], sort_keys=True)}",
            f"- Resonance Energy spent: {json.dumps(resonance['spent'], sort_keys=True)}",
            f"- Resonance Energy wasted: {json.dumps(resonance['wasted'], sort_keys=True)}",
            f"- Resonance Energy final: {json.dumps(resonance['final'], sort_keys=True)}",
            f"- Concerto initial: {json.dumps(concerto['initial'], sort_keys=True)}",
            f"- Concerto gained: {json.dumps(concerto['gained'], sort_keys=True)}",
            f"- Concerto spent: {json.dumps(concerto['spent'], sort_keys=True)}",
            f"- Concerto wasted: {json.dumps(concerto['wasted'], sort_keys=True)}",
            f"- Concerto final: {json.dumps(concerto['final'], sort_keys=True)}",
            "",
            "## Damage Categories",
            "",
        ]
    )
    for category, value in categories.items():
        lines.append(f"- {category}: {value}")
    lines.extend(
        [
            f"- Category sum: {sum(categories.values())}",
            "",
            "## Active Echo Damage",
            "",
        ]
    )
    for action_id in ("aemeath_echo_sigillum", "lynae_echo_hyvatia", "mornye_echo_reactor_husk"):
        lines.append(f"- {action_id}: {json.dumps(echo_summary[action_id], sort_keys=True)}")
    lines.extend(
        [
            f"- Total active Echo damage: {echo_summary['total_active_echo_damage']}",
            "",
            "## Uptime",
            "",
            f"- Everbright Polestar liberation penetration uptime: {uptime['everbright_polestar_liberation_penetration_uptime_seconds']}",
            f"- Aemeath Trailblazing Star 5-set uptime: {uptime['aemeath_trailblazing_star_5set_uptime_seconds']}",
            f"- Mornye Halo of Starry Radiance 5-set uptime: {uptime['mornye_halo_of_starry_radiance_5set_uptime_seconds']}",
            "",
            "## Fields And Cutoff",
            "",
            f"- Mornye field event summary: {json.dumps(primary['mornye_field_summary'], sort_keys=True)}",
            f"- Lynae Spray Paint event summary: {json.dumps(primary['lynae_spray_paint_summary'], sort_keys=True)}",
            f"- Remaining scheduled effects at cutoff, not counted after 120: {len(primary['remaining_scheduled_effects_at_cutoff'])}",
            f"- Final clipped action excluded damage: {primary['final_clipped_action']['damage_after_cutoff_excluded']}",
            "",
            "## Known Limits",
            "",
            "- Opening Aemeath -> Mornye normal swap still uses the known 0.50s placeholder.",
            "- Mornye exact dodge-cancel next-input frame remains unresolved.",
            "- Source-unconfirmed active-Echo Off-Tune values, including Lynae Hyvatia, remain unresolved.",
            "- Final cutoff uses the existing runtime clip; post-120 scheduled effects remain uncounted.",
            "",
        ]
    )
    return "\n".join(lines)


def _comparison_payload(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    primary = results["primary"]
    comparisons = {}
    for name, result in results.items():
        delta = result["total_damage"] - primary["total_damage"]
        comparisons[name] = {
            "total_damage": result["total_damage"],
            "dps": result["dps"],
            "delta_vs_primary_damage": delta,
            "delta_vs_primary_percent": (delta / primary["total_damage"]) * 100.0,
            "damage_by_character": result["damage_by_character"],
            "action_count": result["selected_action_count"],
            "placeholder_count": result["placeholder_fallback"]["count"],
            "tune_break_times": [item["combat_time"] for item in result["tune_breaks"]],
            "major_field_event_count": len(result["mornye_field_events"]),
            "route_hash": result["selected_sequence_sha256"],
            "known_limitations": result["known_limitations"],
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "source_baseline_label": SOURCE_BASELINE_LABEL,
        "candidate_label": CANDIDATE_LABEL,
        "external_review_status": "pending",
        "comparisons": comparisons,
    }


def _render_comparison_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Manual 120-Second Baseline Comparisons",
        "",
        "These deterministic controls are references only; no result is promoted as a best policy.",
        "",
    ]
    primary_damage = payload["comparisons"]["primary"]["total_damage"]
    for name, item in payload["comparisons"].items():
        lines.extend(
            [
                f"## {name}",
                "",
                f"- Total damage: {item['total_damage']}",
                f"- DPS: {item['dps']}",
                f"- Delta vs primary: {item['delta_vs_primary_damage']} ({item['delta_vs_primary_percent']}%)",
                f"- Action count: {item['action_count']}",
                f"- Placeholder count: {item['placeholder_count']}",
                f"- Tune Break times: {item['tune_break_times']}",
                f"- Route hash: `{item['route_hash']}`",
                "",
            ]
        )
    lines.append(f"Primary reference damage: {primary_damage}")
    lines.append("")
    return "\n".join(lines)


def write_outputs() -> dict[str, Any]:
    routes = _write_route_file()
    results = {name: execute_route(name, routes_payload=routes) for name in routes["routes"]}
    primary = results["primary"]
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(primary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_timeline_csv(primary)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(_render_report(primary), encoding="utf-8")
    comparisons = _comparison_payload(results)
    COMPARISONS_PATH.write_text(json.dumps(comparisons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    COMPARISONS_REPORT_PATH.write_text(_render_comparison_report(comparisons), encoding="utf-8")
    return {"routes": routes, "results": results, "comparisons": comparisons}


def assert_primary_contract(result: dict[str, Any]) -> None:
    assert result["selected_action_sequence" if False else "selected_action_count"] == len(ROUTE_DEFINITIONS["primary"]["selected"])
    assert_close(result["final_combat_time"], TARGET_COMBAT_TIME, "primary final combat time")
    assert result["total_damage"] > 0.0
    assert_close(result["dps"], result["total_damage"] / TARGET_COMBAT_TIME, "primary DPS")
    route = _load_routes_or_defaults()["routes"]["primary"]
    assert route["selected_policy_actions"][:41] == SELECTED_ROUTE
    assert route["expected_resolved_actions"][:41] == EXPECTED_RESOLVED_ROUTE
    assert "short_wait" not in route["selected_policy_actions"]
    assert "short_wait" not in route["expected_resolved_actions"]
    assert result["placeholder_fallback"]["count"] == 1
    assert result["placeholder_fallback"]["steps"][0]["step"] == 6
    assert result["final_clipped_action"]["truncated_by_combat_limit"] is True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-results", action="store_true")
    args = parser.parse_args(argv)
    if args.write_results:
        output = write_outputs()
        primary = output["results"]["primary"]
    else:
        primary = execute_route("primary")
    print(
        json.dumps(
            {
                "status": "implemented_tests_passed_pending_external_review",
                "final_combat_time": primary["final_combat_time"],
                "total_damage": primary["total_damage"],
                "dps": primary["dps"],
                "selected_action_count": primary["selected_action_count"],
                "selected_sequence_sha256": primary["selected_sequence_sha256"],
                "resolved_sequence_sha256": primary["resolved_sequence_sha256"],
                "placeholder_fallback": primary["placeholder_fallback"],
                "final_clipped_action": primary["final_clipped_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
