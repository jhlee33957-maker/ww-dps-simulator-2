from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from simulator.models import ActionData, CombatState
from simulator.resource_system import consume_concerto, is_concerto_ready, sync_concerto_state
from simulator.roster import get_swap_target_character_id


PLACEHOLDER_WARNING = (
    "Generic swap timing is a placeholder for party-structure testing. "
    "It is not sourced from Excel/client data. Real party DPS requires "
    "QTE/Intro/Outro transition modeling."
)


@dataclass
class TransitionResolution:
    outgoing_character_id: str
    incoming_character_id: str
    transition_type: str
    transition_reason: str
    outgoing_concerto_before: float
    outgoing_concerto_ready: bool
    outgoing_concerto_consumed: bool
    outgoing_concerto_after: float
    incoming_qte_candidate_id: str | None
    incoming_qte_mode: str | None
    incoming_qte_applied: bool
    outgoing_outro_applied: bool
    action_time: float
    combat_time_cost: float
    swap_timing_source: str
    swap_timing_is_placeholder: bool
    fallback_swap_used: bool
    transition_events: list[dict[str, Any]] = field(default_factory=list)
    outgoing_outro_event_id: str | None = None
    incoming_intro_event_id: str | None = None
    warnings: list[str] = field(default_factory=list)


def default_transition_config() -> dict[str, Any]:
    return {
        "version": 1,
        "generic_swap_fallback": {
            "action_time": 0.5,
            "combat_time_cost": 0.5,
            "is_placeholder": True,
            "source": "built_in_generic_swap_fallback",
            "warning": PLACEHOLDER_WARNING,
        },
        "concerto_transition": {
            "enabled": True,
            "default_concerto_cap": 100.0,
            "qte_mode": "disabled",
            "qte_modes": ["disabled", "dry_run", "enabled"],
            "consume_concerto_on_enabled_transition": True,
            "consume_concerto_on_dry_run": False,
            "consume_concerto_on_disabled": False,
            "normal_swap_when_concerto_not_ready": True,
        },
        "characters": {},
    }


def load_transition_config(data_dir: Path | str) -> dict[str, Any]:
    path = Path(data_dir) / "transition_config.json"
    if not path.exists():
        return default_transition_config()
    with path.open("r", encoding="utf-8-sig") as file:
        config = json.load(file)
    merged = default_transition_config()
    merged.update(config)
    merged["generic_swap_fallback"] = {
        **default_transition_config()["generic_swap_fallback"],
        **config.get("generic_swap_fallback", {}),
    }
    merged["concerto_transition"] = {
        **default_transition_config()["concerto_transition"],
        **config.get("concerto_transition", {}),
    }
    merged["characters"] = config.get("characters", {})
    merged["_data_dir"] = str(path.parent)
    return merged


def fallback_swap_timing(
    transition_config: dict[str, Any],
    preset_generic_swap: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fallback = dict(transition_config.get("generic_swap_fallback") or {})
    fallback.update(preset_generic_swap or {})
    fallback.setdefault("action_time", 0.5)
    fallback.setdefault("combat_time_cost", fallback["action_time"])
    fallback.setdefault("is_placeholder", True)
    fallback.setdefault("source", "generic_swap_fallback")
    fallback.setdefault("warning", PLACEHOLDER_WARNING)
    return fallback


def build_transition_swap_action(
    selected_action: ActionData,
    transition_config: dict[str, Any],
    preset_generic_swap: dict[str, Any] | None = None,
) -> ActionData:
    fallback = fallback_swap_timing(transition_config, preset_generic_swap)
    action_time = float(fallback["action_time"])
    combat_time_cost = float(fallback.get("combat_time_cost", action_time))
    return ActionData(
        id=selected_action.id,
        name=selected_action.name,
        character_id=selected_action.character_id,
        action_type="swap",
        duration=max(action_time, 0.001),
        action_time=max(action_time, 0.001),
        combat_time_cost=max(combat_time_cost, 0.0),
        cooldown=0.0,
        damage_multiplier=0.0,
        tune_break_multiplier=0.0,
        tune_break_boost_points=0.0,
        resonance_energy_cost=0.0,
        tags=sorted(set([*selected_action.tags, "swap", "party-transition"])),
        policy_selectable=selected_action.policy_selectable,
        data_status="transition_request",
        notes=(
            "Generic party swap transition request. Timing is resolved from "
            "transition_config/preset fallback metadata, not legacy action data."
        ),
    )


def resolve_party_transition(
    selected_action: ActionData,
    state: CombatState,
    actions: dict[str, ActionData],
    transition_config: dict[str, Any],
    preset_generic_swap: dict[str, Any] | None = None,
) -> TransitionResolution:
    incoming_character_id = get_swap_target_character_id(selected_action)
    if incoming_character_id is None:
        raise ValueError(f"Swap action {selected_action.id!r} does not declare a target character.")
    outgoing_character_id = state.active_character_id
    fallback = fallback_swap_timing(transition_config, preset_generic_swap)
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    concerto_config = dict(transition_config.get("concerto_transition") or {})
    default_cap = float(concerto_config.get("default_concerto_cap", 100.0) or 100.0)
    outgoing_state = sync_concerto_state(state, outgoing_character_id, default_cap=default_cap)
    outgoing_concerto_before = float(outgoing_state["concerto_energy"])
    outgoing_ready = is_concerto_ready(outgoing_state)
    qte_mode = _qte_mode(concerto_config)
    incoming_qte_candidate_id: str | None = None
    incoming_qte_applied = False
    outgoing_outro_applied = False
    outgoing_concerto_consumed = False
    transition_type = "full_concerto_transition" if outgoing_ready else "normal_swap"
    transition_reason = "concerto_ready" if outgoing_ready else "concerto_not_ready"

    outgoing_event = None
    incoming_event = None
    if outgoing_ready or not bool(concerto_config.get("enabled", True)):
        outgoing_event = _transition_event(
            transition_config,
            character_id=outgoing_character_id,
            section="outro",
            event_type="outro",
            actions=actions,
        )
        incoming_event = _transition_event(
            transition_config,
            character_id=incoming_character_id,
            section="intro_qte",
            event_type="intro_qte",
            actions=actions,
        )
        if outgoing_event is not None:
            outgoing_event["applied"] = True
            events.append(outgoing_event)
            outgoing_outro_applied = True
        qte_candidate, qte_candidate_warnings = _incoming_qte_candidate(
            transition_config,
            state,
            incoming_character_id,
        )
        warnings.extend(qte_candidate_warnings)
        if qte_candidate is not None:
            incoming_qte_candidate_id = str(qte_candidate.get("candidate_id") or qte_candidate.get("proposed_action_id"))
            candidate_event = _qte_candidate_event(qte_candidate, qte_mode)
            if qte_mode == "dry_run":
                events.append(candidate_event)
            elif qte_mode == "enabled":
                candidate_event["implementation_status"] = "not_implemented"
                candidate_event["notes"] = (
                    "Aemeath QTE enabled mode is scaffolded only; candidate remains review-only "
                    "and is not applied to damage, timing, resources, or state."
                )
                events.append(candidate_event)
                warnings.append("incoming_qte_enabled_not_implemented")
        if incoming_event is not None:
            incoming_event["applied"] = True
            events.append(incoming_event)
            incoming_qte_applied = incoming_event.get("event_type") == "intro_qte"
    else:
        qte_mode = "disabled"

    consume_enabled = (
        outgoing_ready
        and qte_mode == "enabled"
        and bool(concerto_config.get("consume_concerto_on_enabled_transition", True))
        and any(bool(event.get("qte_applied", False)) or bool(event.get("consume_concerto_on_apply", False)) for event in events)
    )
    if consume_enabled:
        consume_concerto(outgoing_state)
        state.concerto_energy[outgoing_character_id] = float(outgoing_state["concerto_energy"])
        outgoing_concerto_consumed = True

    timed_events = [
        event for event in events
        if bool(event.get("affects_timing", True))
        if float(event.get("action_time", 0.0) or 0.0) > 0.0
        or float(event.get("combat_time_cost", 0.0) or 0.0) > 0.0
    ]
    if timed_events:
        primary = timed_events[0]
        action_time = float(primary.get("action_time", 0.0) or 0.0)
        combat_time_cost = float(primary.get("combat_time_cost", action_time) or 0.0)
        timing_source = str(primary.get("action_id") or primary.get("source") or "transition_event")
        is_placeholder = bool(primary.get("is_placeholder", False))
        fallback_used = False
    else:
        action_time = float(fallback["action_time"])
        combat_time_cost = float(fallback.get("combat_time_cost", action_time))
        timing_source = str(fallback.get("source", "generic_swap_fallback"))
        is_placeholder = bool(fallback.get("is_placeholder", True))
        fallback_used = True
        warning = str(fallback.get("warning") or PLACEHOLDER_WARNING)
        if warning:
            warnings.append(warning)

    return TransitionResolution(
        outgoing_character_id=outgoing_character_id,
        incoming_character_id=incoming_character_id,
        transition_type=transition_type,
        transition_reason=transition_reason,
        outgoing_concerto_before=outgoing_concerto_before,
        outgoing_concerto_ready=outgoing_ready,
        outgoing_concerto_consumed=outgoing_concerto_consumed,
        outgoing_concerto_after=float(outgoing_state["concerto_energy"]),
        incoming_qte_candidate_id=incoming_qte_candidate_id,
        incoming_qte_mode=qte_mode,
        incoming_qte_applied=incoming_qte_applied,
        outgoing_outro_applied=outgoing_outro_applied,
        action_time=action_time,
        combat_time_cost=combat_time_cost,
        swap_timing_source=timing_source,
        swap_timing_is_placeholder=is_placeholder,
        fallback_swap_used=fallback_used,
        transition_events=events,
        outgoing_outro_event_id=outgoing_event.get("action_id") if outgoing_event else None,
        incoming_intro_event_id=incoming_event.get("action_id") if incoming_event else None,
        warnings=warnings,
    )


def _transition_event(
    transition_config: dict[str, Any],
    *,
    character_id: str,
    section: str,
    event_type: str,
    actions: dict[str, ActionData],
) -> dict[str, Any] | None:
    character_config = (transition_config.get("characters") or {}).get(character_id, {})
    event_config = character_config.get(section) or {}
    if not event_config.get("enabled", False):
        return None

    action_id = event_config.get("action_id")
    action = actions.get(action_id) if action_id else None
    applies_buffs = list(event_config.get("applies_buffs") or getattr(action, "applies_buffs", []) or [])
    action_time = float(event_config.get("action_time", 0.0))
    combat_time_cost = float(event_config.get("combat_time_cost", action_time))
    return {
        "event_type": event_type,
        "character_id": character_id,
        "action_id": action_id,
        "implementation_status": event_config.get("implementation_status", "unimplemented"),
        "enabled": True,
        "applied": True,
        "affects_timing": True,
        "requires_concerto": bool(event_config.get("requires_concerto", True)),
        "action_time": action_time,
        "combat_time_cost": combat_time_cost,
        "applies_buffs": applies_buffs,
        "is_placeholder": bool(event_config.get("is_placeholder", False)),
        "source": event_config.get("source", "transition_config"),
        "notes": event_config.get("notes"),
    }


def _qte_mode(concerto_config: dict[str, Any]) -> str:
    qte_mode = str(concerto_config.get("qte_mode", "disabled"))
    allowed = set(concerto_config.get("qte_modes") or ["disabled", "dry_run", "enabled"])
    return qte_mode if qte_mode in allowed else "disabled"


def _incoming_qte_candidate(
    transition_config: dict[str, Any],
    state: CombatState,
    incoming_character_id: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    if incoming_character_id != "aemeath":
        return None, []

    character_config = (transition_config.get("characters") or {}).get(incoming_character_id, {})
    intro_config = character_config.get("intro_qte") or {}
    candidate_source = intro_config.get("candidate_source") or intro_config.get("source")
    if not candidate_source:
        return None, ["incoming_qte_candidate_source_missing"]

    source_path = Path(candidate_source)
    if not source_path.is_absolute():
        data_dir = Path(str(transition_config.get("_data_dir") or "data"))
        source_path = data_dir / source_path
        if not source_path.exists() and str(candidate_source).startswith("data/"):
            source_path = data_dir.parent / str(candidate_source)
    if not source_path.exists():
        return None, [f"incoming_qte_candidate_source_missing:{candidate_source}"]

    with source_path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)
    candidates = payload.get("candidates") or []
    candidates_by_id = {
        str(candidate.get("candidate_id") or candidate.get("proposed_action_id")): candidate
        for candidate in candidates
    }
    aemeath_state = state.character_states.get("aemeath") or state.character_mechanics_state.get("aemeath") or {}
    form = aemeath_state.get("form")
    warnings: list[str] = []
    if form == "mech":
        candidate_id = "aemeath_qte_intro_mech"
    elif form in {"aemeath", "human"}:
        candidate_id = "aemeath_qte_intro_human"
    else:
        candidate_id = "aemeath_qte_intro_human"
        warnings.append("incoming_qte_aemeath_form_missing_defaulted_human")
    candidate = candidates_by_id.get(candidate_id)
    if candidate is None:
        warnings.append(f"incoming_qte_candidate_missing:{candidate_id}")
    return candidate, warnings


def _qte_candidate_event(candidate: dict[str, Any], qte_mode: str) -> dict[str, Any]:
    timing = candidate.get("timing_candidate") or {}
    damage = candidate.get("damage_candidate") or {}
    notice = candidate.get("notice_metadata") or {}
    candidate_id = str(candidate.get("candidate_id") or candidate.get("proposed_action_id"))
    return {
        "event_type": "intro_qte",
        "character_id": "aemeath",
        "action_id": candidate.get("proposed_action_id") or candidate_id,
        "candidate_id": candidate_id,
        "implementation_status": "dry_run" if qte_mode == "dry_run" else "review_only",
        "enabled": qte_mode == "enabled",
        "applied": False,
        "affects_timing": False,
        "qte_mode": qte_mode,
        "qte_applied": False,
        "action_time": float(timing.get("action_time_seconds", 0.0) or 0.0),
        "combat_time_cost": float(timing.get("combat_time_cost_seconds", 0.0) or 0.0),
        "action_time_frames": timing.get("action_time_frames"),
        "combat_time_cost_frames": timing.get("combat_time_cost_frames"),
        "parsed_multipliers": damage.get("parsed_multipliers", []),
        "trigger_classification": damage.get("trigger_classification"),
        "source_damage_label": damage.get("source_damage_label"),
        "damage_bonus_category": damage.get("damage_bonus_category"),
        "previous_outro_trigger_frame": notice.get("previous_character_outro_trigger_frame")
        or timing.get("previous_outro_trigger_frame"),
        "previous_outro_trigger_frames": notice.get("previous_outro_trigger_frames")
        or timing.get("previous_outro_trigger_frames", []),
        "source": "data/extracted/aemeath_qte_action_candidates.json",
        "notes": "Aemeath QTE candidate logged only; no damage, timing, resources, or state changes are applied.",
    }
