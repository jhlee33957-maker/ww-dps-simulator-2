from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from simulator.models import ActionData, HitData


class TransitionActionError(ValueError):
    pass


def load_transition_actions(data_dir: Path | str) -> dict[str, dict[str, Any]]:
    path = Path(data_dir) / "transition_actions.json"
    return _load_transition_actions_cached(str(path.resolve()))


@lru_cache(maxsize=8)
def _load_transition_actions_cached(path_text: str) -> dict[str, dict[str, Any]]:
    path = Path(path_text)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as file:
        records = json.load(file)
    actions: dict[str, dict[str, Any]] = {}
    for record in records:
        _validate_transition_action_record(record)
        actions[str(record["id"])] = record
    return actions


def list_transition_actions(data_dir: Path | str) -> list[dict[str, Any]]:
    return list(load_transition_actions(data_dir).values())


def get_transition_action(data_dir: Path | str, action_id: str) -> dict[str, Any] | None:
    return load_transition_actions(data_dir).get(action_id)


def transition_action_to_action_data(record: dict[str, Any]) -> ActionData:
    _validate_transition_action_record(record)
    action_time = float(record["action_time"])
    combat_time_cost = float(record["combat_time_cost"])
    damage_bonus_category = str(record.get("damage_bonus_category") or "")
    trigger_classification = str(record.get("trigger_classification") or "")
    metadata = dict(record.get("metadata") or {})
    raw_skill_category = record.get("raw_skill_category", metadata.get("raw_skill_category"))
    raw_damage_type = record.get("raw_damage_type", metadata.get("raw_damage_type"))
    damage_element = record.get("damage_element", record.get("element"))
    tags = [
        "transition",
        "party-transition",
        "intro",
        str(record["transition_event_type"]),
        trigger_classification,
        str(record.get("source_damage_label") or ""),
        str(record.get("element") or ""),
    ]
    if "qte" in trigger_classification:
        tags.append("qte")
    if damage_bonus_category and damage_bonus_category != "none_or_unmodeled_intro":
        tags.append(damage_bonus_category)

    mechanic_effects = dict(record.get("mechanic_effects") or {})
    mechanic_effects.update(
        {
            "transition_action": True,
            "transition_action_id": record["id"],
            "transition_actor_character_id": record["character_id"],
            "skip_character_after_action": not bool(record.get("apply_character_mechanics", False)),
            "damage_bonus_category": damage_bonus_category,
        }
    )

    return ActionData(
        id=f"transition:{record['id']}",
        name=str(record.get("name") or record["id"]),
        character_id=str(record["character_id"]),
        action_type="swap",
        duration=max(action_time, 0.001),
        action_time=max(action_time, 0.001),
        combat_time_cost=max(combat_time_cost, 0.0),
        cooldown=0.0,
        damage_multiplier=0.0,
        tune_break_multiplier=0.0,
        off_tune_value=float(record.get("off_tune_value", 0.0) or 0.0),
        off_tune_value_source_status=record.get("off_tune_value_source_status"),
        off_tune_value_source_ref=record.get("off_tune_value_source_ref"),
        damage_bonus_category=record.get("damage_bonus_category"),
        damage_element=damage_element,
        raw_skill_category=raw_skill_category,
        raw_damage_type=raw_damage_type,
        damage_bonus_category_source=record.get("damage_bonus_category_source"),
        scaling_stat=record.get("scaling_stat"),
        scaling_stat_source=record.get("scaling_stat_source"),
        scaling_stat_source_status=record.get("scaling_stat_source_status"),
        scaling_stat_note=record.get("scaling_stat_note"),
        resonance_energy_gain=float(record.get("resonance_energy_gain", 0.0) or 0.0),
        concerto_energy_gain=float(record.get("concerto_energy_gain", 0.0) or 0.0),
        resonance_energy_cost=0.0,
        hits=_transition_hits(record),
        mechanic_event_tags=list(record.get("mechanic_event_tags") or []),
        mechanic_event_triggers=list(record.get("mechanic_event_triggers") or []),
        tags=sorted({tag for tag in tags if tag}),
        policy_selectable=False,
        mechanic_effects=mechanic_effects,
        data_status="transition_only",
        notes="Non-policy transition action loaded from data/transition_actions.json.",
    )


def transition_action_event(record: dict[str, Any], *, qte_mode: str, applied: bool) -> dict[str, Any]:
    metadata = dict(record.get("metadata") or {})
    flow_light = metadata.get("flow_light_state_grant_review_only")
    return {
        "event_type": record["transition_event_type"],
        "character_id": record["character_id"],
        "action_id": record["id"],
        "transition_action_id": record["id"],
        "candidate_id": record["id"],
        "implementation_status": "implemented" if applied else "review_only",
        "enabled": qte_mode == "enabled",
        "applied": applied,
        "affects_timing": applied,
        "qte_mode": qte_mode,
        "qte_applied": applied,
        "incoming_intro_mode": qte_mode,
        "incoming_intro_applied": applied,
        "incoming_intro_candidate_id": record["id"],
        "consume_concerto_on_apply": applied,
        "action_time": float(record["action_time"]),
        "combat_time_cost": float(record["combat_time_cost"]),
        "parsed_multipliers": _multipliers(record),
        "trigger_classification": record.get("trigger_classification"),
        "source_damage_label": record.get("source_damage_label"),
        "damage_bonus_category": record.get("damage_bonus_category"),
        "previous_outro_trigger_frame": record.get("previous_outro_trigger_frame"),
        "flow_light_metadata_present": flow_light is not None,
        "flow_light_applied": False,
        "metadata": metadata,
        "source": record.get("review_source", "data/transition_actions.json"),
        "notes": (
            "Transition QTE action applied through the generic transition action pipeline."
            if applied
            else "Transition QTE candidate logged only; no damage, timing, resources, or state changes are applied."
        ),
    }


def _transition_hits(record: dict[str, Any]) -> list[HitData]:
    multipliers = _multipliers(record)
    action_time = float(record["action_time"])
    count = len(multipliers)
    if count <= 0:
        return []
    return [
        HitData(
            time=action_time * (index + 1) / count,
            damage_category="normal",
            damage_multiplier=multiplier,
            tags=["qte", "intro", str(record.get("damage_bonus_category") or "")],
            name=f"{record['id']} hit {index + 1}",
        )
        for index, multiplier in enumerate(multipliers)
    ]


def _multipliers(record: dict[str, Any]) -> list[float]:
    return [
        float(item.get("damage_multiplier", item) if isinstance(item, dict) else item)
        for item in record.get("hits", [])
    ]


def _validate_transition_action_record(record: dict[str, Any]) -> None:
    action_id = record.get("id")
    if not action_id:
        raise TransitionActionError("Transition action is missing id.")
    if record.get("transition_only") is not True:
        raise TransitionActionError(f"Transition action {action_id!r} must set transition_only=true.")
    if record.get("policy_selectable") is not False:
        raise TransitionActionError(f"Transition action {action_id!r} must set policy_selectable=false.")
    if float(record.get("action_time", 0.0) or 0.0) <= 0.0:
        raise TransitionActionError(f"Transition action {action_id!r} must define positive action_time.")
    if float(record.get("combat_time_cost", -1.0) or 0.0) < 0.0:
        raise TransitionActionError(f"Transition action {action_id!r} must define non-negative combat_time_cost.")
    if record.get("transition_event_type") not in {"outgoing_outro", "incoming_intro_qte", "fallback_swap"}:
        raise TransitionActionError(f"Transition action {action_id!r} has unsupported transition_event_type.")
    if record.get("transition_event_type") == "incoming_intro_qte" and not _multipliers(record):
        raise TransitionActionError(f"Transition action {action_id!r} must define QTE hit multipliers.")
    if _multipliers(record):
        scaling_stat = record.get("scaling_stat")
        if scaling_stat not in {"atk", "def", "hp", "unresolved"}:
            raise TransitionActionError(
                f"Transition action {action_id!r} has direct damage and must set scaling_stat to "
                "atk, def, hp, or unresolved."
            )
