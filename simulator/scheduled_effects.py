from __future__ import annotations

from collections.abc import Callable
from typing import Any

from simulator.models import ActionData, CombatState, ScheduledEffectState


SCHEDULER_EPSILON = 1e-9


def validate_scheduled_effect_request(
    *,
    source_character_id: str,
    payload_action_id: str,
    actions: dict[str, ActionData],
    selected_character_ids: set[str],
    remaining_duration: float,
    tick_interval: float,
    time_until_next_tick: float,
    trigger_count: int = 0,
    max_trigger_count: int | None = None,
    payload_event_type: str = "damage",
    scheduled_resource_policy: str = "none",
) -> None:
    if source_character_id not in selected_character_ids:
        raise ValueError(f"Unknown scheduled-effect source character {source_character_id!r}")
    if payload_action_id not in actions:
        raise ValueError(f"Unknown scheduled-effect payload action {payload_action_id!r}")
    payload = actions[payload_action_id]
    if payload.policy_selectable:
        raise ValueError(f"Scheduled-effect payload action {payload_action_id!r} must not be policy selectable")
    if remaining_duration <= 0.0:
        raise ValueError("Scheduled-effect remaining_duration must be > 0")
    if tick_interval <= 0.0:
        raise ValueError("Scheduled-effect tick_interval must be > 0")
    if time_until_next_tick < 0.0:
        raise ValueError("Scheduled-effect time_until_next_tick must be >= 0")
    if trigger_count < 0:
        raise ValueError("Scheduled-effect trigger_count must be >= 0")
    if max_trigger_count is not None and max_trigger_count <= 0:
        raise ValueError("Scheduled-effect max_trigger_count must be > 0 when present")
    if payload_event_type not in {"damage", "healing", "status_application"}:
        raise ValueError(f"Unsupported scheduled payload event type {payload_event_type!r}")
    if payload_event_type in {"healing", "status_application"} and scheduled_resource_policy != "none":
        raise ValueError("Scheduled healing/status payloads must not grant scheduled resources")
    if scheduled_resource_policy not in {"none", "source_confirmed_positive_gains"}:
        raise ValueError(f"Unsupported scheduled_resource_policy {scheduled_resource_policy!r}")


def schedule_effect(
    state: CombatState,
    *,
    actions: dict[str, ActionData],
    selected_character_ids: set[str],
    instance_id: str,
    effect_id: str,
    source_character_id: str,
    source_action_id: str | None,
    payload_action_id: str,
    remaining_duration: float,
    tick_interval: float,
    time_until_next_tick: float | None = None,
    activation_combat_time: float = 0.0,
    trigger_on_apply: bool = False,
    trigger_count: int = 0,
    max_trigger_count: int | None = None,
    refresh_rule: str = "replace",
    payload_event_type: str = "damage",
    scheduled_resource_policy: str = "none",
    source_status: str,
    source_ref: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if refresh_rule not in {"replace", "refresh_duration", "keep_existing"}:
        raise ValueError(f"Unsupported scheduled-effect refresh_rule {refresh_rule!r}")
    if time_until_next_tick is None:
        time_until_next_tick = tick_interval
    activation_combat_time = max(0.0, float(activation_combat_time or 0.0))
    validate_scheduled_effect_request(
        source_character_id=source_character_id,
        payload_action_id=payload_action_id,
        actions=actions,
        selected_character_ids=selected_character_ids,
        remaining_duration=remaining_duration,
        tick_interval=tick_interval,
        time_until_next_tick=time_until_next_tick,
        trigger_count=trigger_count,
        max_trigger_count=max_trigger_count,
        payload_event_type=payload_event_type,
        scheduled_resource_policy=scheduled_resource_policy,
    )

    existing_index = next(
        (index for index, effect in enumerate(state.scheduled_effects) if effect.instance_id == instance_id),
        None,
    )
    existing = state.scheduled_effects[existing_index] if existing_index is not None else None
    if existing is not None and refresh_rule == "keep_existing":
        return {
            "status": "retained",
            "operation": "kept_existing",
            "effect": existing,
            "activation_combat_time": existing.activation_combat_time,
            "immediate_trigger_pending": False,
            "immediate_trigger_executed": False,
        }
    if existing is not None and refresh_rule == "refresh_duration":
        existing.remaining_duration = float(remaining_duration)
        return {
            "status": "refreshed",
            "operation": "refreshed",
            "effect": existing,
            "activation_combat_time": existing.activation_combat_time,
            "immediate_trigger_pending": False,
            "immediate_trigger_executed": False,
        }

    insertion_order = state.scheduled_effect_next_order
    state.scheduled_effect_next_order += 1
    replacement = ScheduledEffectState(
        instance_id=instance_id,
        effect_id=effect_id,
        source_character_id=source_character_id,
        source_action_id=source_action_id,
        payload_action_id=payload_action_id,
        activation_combat_time=activation_combat_time,
        remaining_duration=float(remaining_duration),
        tick_interval=float(tick_interval),
        time_until_next_tick=float(tick_interval if trigger_on_apply else time_until_next_tick),
        trigger_on_apply_pending=bool(trigger_on_apply),
        trigger_count=int(trigger_count),
        max_trigger_count=max_trigger_count,
        refresh_rule=refresh_rule,  # type: ignore[arg-type]
        source_status=source_status,
        source_ref=source_ref,
        payload_event_type=payload_event_type,  # type: ignore[arg-type]
        scheduled_resource_policy=scheduled_resource_policy,  # type: ignore[arg-type]
        metadata=dict(metadata or {}),
        insertion_order=insertion_order,
    )
    if existing_index is None:
        state.scheduled_effects.append(replacement)
        return {
            "status": "scheduled",
            "operation": "created",
            "effect": replacement,
            "activation_combat_time": activation_combat_time,
            "immediate_trigger_pending": bool(trigger_on_apply),
            "immediate_trigger_executed": False,
        }
    state.scheduled_effects[existing_index] = replacement
    return {
        "status": "replaced",
        "operation": "replaced",
        "effect": replacement,
        "activation_combat_time": activation_combat_time,
        "immediate_trigger_pending": bool(trigger_on_apply),
        "immediate_trigger_executed": False,
    }


def remove_scheduled_effect(state: CombatState, instance_id: str) -> ScheduledEffectState | None:
    for index, effect in enumerate(state.scheduled_effects):
        if effect.instance_id == instance_id:
            return state.scheduled_effects.pop(index)
    return None


def scheduled_effect_by_instance_id(state: CombatState, instance_id: str) -> ScheduledEffectState | None:
    for effect in state.scheduled_effects:
        if effect.instance_id == instance_id:
            return effect
    return None


def advance_scheduled_effects(
    state: CombatState,
    *,
    combat_start_time: float,
    combat_elapsed: float,
    host_action_id: str,
    execute_tick: Callable[[ScheduledEffectState, float, float, int], dict[str, Any]],
) -> dict[str, Any]:
    combat_elapsed = max(0.0, float(combat_elapsed or 0.0))
    if combat_elapsed <= SCHEDULER_EPSILON or not state.scheduled_effects:
        return {
            "scheduled_damage": 0.0,
            "scheduled_damage_events": [],
            "scheduled_healing_events": [],
            "scheduled_status_application_events": [],
        }

    combat_end_time = combat_start_time + combat_elapsed
    due_events: list[tuple[float, int, str, str, int]] = []
    periodic_counts: dict[str, int] = {}
    active_elapsed_by_instance: dict[str, float] = {}
    pending_due: set[str] = set()
    for effect in list(state.scheduled_effects):
        activation_time = max(0.0, float(effect.activation_combat_time or 0.0))
        if activation_time > combat_end_time + SCHEDULER_EPSILON:
            periodic_counts[effect.instance_id] = 0
            active_elapsed_by_instance[effect.instance_id] = 0.0
            continue
        active_start_time = max(float(combat_start_time), activation_time)
        active_start_offset = max(0.0, active_start_time - float(combat_start_time))
        active_elapsed = max(0.0, combat_end_time - active_start_time)
        active_elapsed_by_instance[effect.instance_id] = active_elapsed
        simulated_count = 0
        if effect.trigger_on_apply_pending:
            pending_offset = max(0.0, activation_time - float(combat_start_time))
            if pending_offset <= combat_elapsed + SCHEDULER_EPSILON:
                if effect.max_trigger_count is None or effect.trigger_count < effect.max_trigger_count:
                    simulated_count += 1
                    pending_due.add(effect.instance_id)
                    due_events.append((pending_offset, effect.insertion_order, effect.instance_id, "trigger_on_apply", 0))
        phase = float(effect.tick_interval if effect.instance_id in pending_due else effect.time_until_next_tick)
        local_periodic_count = 0
        offset = active_start_offset + phase
        while (
            phase <= active_elapsed + SCHEDULER_EPSILON
            and phase <= float(effect.remaining_duration) + SCHEDULER_EPSILON
        ):
            if (
                effect.max_trigger_count is not None
                and effect.trigger_count + simulated_count >= effect.max_trigger_count
            ):
                break
            local_periodic_count += 1
            simulated_count += 1
            due_events.append((max(0.0, offset), effect.insertion_order, effect.instance_id, "periodic", local_periodic_count))
            phase += float(effect.tick_interval)
            offset += float(effect.tick_interval)
        periodic_counts[effect.instance_id] = local_periodic_count

    total_damage = 0.0
    events: list[dict[str, Any]] = []
    healing_events: list[dict[str, Any]] = []
    status_application_events: list[dict[str, Any]] = []
    for offset, _order, instance_id, trigger_kind, local_index in sorted(due_events, key=lambda item: (item[0], item[1], item[2], item[3])):
        effect = scheduled_effect_by_instance_id(state, instance_id)
        if effect is None:
            continue
        if effect.max_trigger_count is not None and effect.trigger_count >= effect.max_trigger_count:
            continue
        trigger_index = int(effect.trigger_count) + 1
        combat_time = combat_start_time + offset
        event = execute_tick(effect, combat_time, offset, trigger_index)
        event.setdefault("host_action_id", host_action_id)
        event.setdefault("host_action_combat_offset", offset)
        event.setdefault("combat_time", combat_time)
        event.setdefault("trigger_index", trigger_index)
        event.setdefault("scheduled_effect_trigger_kind", trigger_kind)
        event.setdefault("scheduled_effect_local_trigger_index", local_index)
        effect.trigger_count = trigger_index
        if trigger_kind == "trigger_on_apply":
            effect.trigger_on_apply_pending = False
            effect.time_until_next_tick = float(effect.tick_interval)
        total_damage += float(event.get("damage", 0.0) or 0.0)
        events.append(event)
        if event.get("event_type") == "scheduled_heal":
            healing_events.append(event)
        if event.get("event_type") == "scheduled_status_application":
            status_application_events.append(event)

    for effect in list(state.scheduled_effects):
        active_elapsed = float(active_elapsed_by_instance.get(effect.instance_id, 0.0) or 0.0)
        triggers = int(periodic_counts.get(effect.instance_id, 0))
        if active_elapsed <= SCHEDULER_EPSILON and triggers <= 0:
            continue
        starting_phase = float(effect.time_until_next_tick)
        effect.time_until_next_tick = max(
            0.0,
            starting_phase - active_elapsed + triggers * float(effect.tick_interval),
        )
        effect.remaining_duration = max(0.0, float(effect.remaining_duration) - active_elapsed)

    state.scheduled_effects = [
        effect
        for effect in state.scheduled_effects
        if effect.remaining_duration > SCHEDULER_EPSILON
        and (
            effect.max_trigger_count is None
            or effect.trigger_count < effect.max_trigger_count
            or effect.metadata.get("remove_on_max_trigger_count") is False
        )
    ]
    return {
        "scheduled_damage": total_damage,
        "scheduled_damage_events": events,
        "scheduled_healing_events": healing_events,
        "scheduled_status_application_events": status_application_events,
    }
