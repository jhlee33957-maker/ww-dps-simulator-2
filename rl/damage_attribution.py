from __future__ import annotations

from collections import Counter, defaultdict
import json
from typing import Any, Iterable


FLOAT_TOLERANCE = 1e-6
SOURCED_DAMAGE_COLLECTIONS = (
    ("scheduled_damage_events", "scheduled_damage"),
    ("tune_response_events", "tune_response_damage"),
    ("generated_mechanic_damage_events", "generated_mechanic_damage"),
)


class DamageAttributionError(RuntimeError):
    pass


def row_damage_attribution(row: Any, *, tolerance: float = FLOAT_TOLERANCE) -> dict[str, Any]:
    mapped = row_mapping(row)
    explicit_by_source: defaultdict[str, float] = defaultdict(float)
    explicit_by_role: defaultdict[str, float] = defaultdict(float)
    explicit_events: list[dict[str, Any]] = []
    seen_events: set[tuple[Any, ...]] = set()
    actor = row_actor_id(mapped)

    for collection_name, role, events in sourced_damage_collections(mapped):
        for event in events:
            event_key = event_identity(collection_name, event)
            if event_key in seen_events:
                continue
            seen_events.add(event_key)
            damage = _float(event.get("damage", 0.0))
            if damage == 0.0:
                continue
            source = str(event.get("source_character_id") or actor)
            explicit_by_source[source] += damage
            explicit_by_role[role] += damage
            explicit_events.append(
                {
                    "collection": collection_name,
                    "role": role,
                    "source_character_id": source,
                    "damage": damage,
                    "event_id": event.get("event_id") or event.get("id"),
                    "payload_action_id": event.get("payload_action_id"),
                    "source_action_id": event.get("source_action_id"),
                    "combat_time": event.get("combat_time"),
                }
            )

    row_damage = row_total_damage(mapped)
    explicit_total = sum(explicit_by_source.values())
    residual = row_damage - explicit_total
    if residual < -tolerance:
        raise DamageAttributionError(
            json.dumps(
                {
                    "reason": "negative residual damage after sourced event attribution",
                    "selected_action_id": mapped.get("selected_action_id"),
                    "resolved_action_id": mapped.get("resolved_action_id"),
                    "row_damage": row_damage,
                    "explicit_event_damage_total": explicit_total,
                    "residual": residual,
                    "explicit_events": explicit_events,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    if residual < 0.0:
        residual = 0.0

    totals: defaultdict[str, float] = defaultdict(float)
    if residual:
        totals[actor] += residual
    for source, damage in explicit_by_source.items():
        totals[source] += damage
    return {
        "selected_action_id": mapped.get("selected_action_id"),
        "resolved_action_id": mapped.get("resolved_action_id"),
        "actor_character_id": actor,
        "row_damage": row_damage,
        "explicit_event_damage_total": explicit_total,
        "explicit_event_damage_by_role": dict(sorted(explicit_by_role.items())),
        "residual_actor_damage": residual,
        "explicit_events": explicit_events,
        "damage_by_character": dict(sorted(totals.items())),
    }


def damage_by_character(rows: Iterable[Any], *, total_damage: float | None = None) -> dict[str, float]:
    totals: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        attribution = row_damage_attribution(row)
        for source, damage in attribution["damage_by_character"].items():
            totals[source] += damage
    result = dict(sorted(totals.items()))
    if total_damage is not None:
        assert_total_close(sum(result.values()), float(total_damage), "damage_by_character total")
    return result


def damage_by_character_and_source(rows: Iterable[Any], *, total_damage: float | None = None) -> dict[str, float]:
    totals: Counter[str] = Counter()
    for row in rows:
        attribution = row_damage_attribution(row)
        actor = attribution["actor_character_id"]
        residual = float(attribution["residual_actor_damage"] or 0.0)
        if residual:
            totals[f"{character_label(actor)} direct action residual"] += residual
        for event in attribution["explicit_events"]:
            source = str(event["source_character_id"])
            role = str(event["role"])
            damage = float(event["damage"])
            totals[f"{character_label(source)} {_role_label(role)}"] += damage
    result = {key: value for key, value in sorted(totals.items()) if value != 0.0}
    if total_damage is not None:
        assert_total_close(sum(result.values()), float(total_damage), "damage_by_character_and_source total")
    return result


def effective_damage_role_breakdown(rows: Iterable[Any], total_damage: float) -> dict[str, float]:
    normal_total = 0.0
    tune_break_total = 0.0
    tune_response_total = 0.0
    generated_total = 0.0
    scheduled_total = 0.0
    row_total = 0.0
    for row in rows:
        mapped = row_mapping(row)
        row_total += row_total_damage(mapped)
        normal_total += row_float(mapped, "normal_damage")
        tune_break_total += row_float(mapped, "tune_break_damage")
        tune_response_total += row_float(mapped, "tune_response_damage")
        generated_total += row_float(mapped, "generated_mechanic_damage")
        scheduled_total += row_float(mapped, "scheduled_damage")
    explicit_total = normal_total + tune_break_total + tune_response_total + generated_total + scheduled_total
    unclassified = float(total_damage) - explicit_total
    role_total = explicit_total + unclassified
    return {
        "schema_version": "effective_damage_role_breakdown_v2",
        "direct_normal_action_damage": normal_total,
        "normal_damage": normal_total,
        "direct_tune_break_damage": tune_break_total,
        "tune_break_damage": tune_break_total,
        "direct_tune_response_damage": tune_response_total,
        "tune_response_damage": tune_response_total,
        "generated_mechanic_damage": generated_total,
        "scheduled_damage": scheduled_total,
        "unclassified_damage": unclassified,
        "raw_timeline_row_total": row_total,
        "classified_damage_before_unclassified": explicit_total,
        "total_damage_check": role_total,
        "reported_total_damage": float(total_damage),
        "total_damage_delta": role_total - float(total_damage),
    }


def sourced_damage_collections(row: Any) -> list[tuple[str, str, list[dict[str, Any]]]]:
    mapped = row_mapping(row)
    return [
        (collection_name, role, [event for event in (mapped.get(collection_name) or []) if isinstance(event, dict)])
        for collection_name, role in SOURCED_DAMAGE_COLLECTIONS
    ]


def row_mapping(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return row
    if hasattr(row, "model_dump"):
        return row.model_dump(mode="json")
    return dict(getattr(row, "__dict__", {}))


def row_actor_id(row: Any) -> str:
    mapped = row_mapping(row)
    return str(
        mapped.get("actor_character_id")
        or mapped.get("character_id")
        or mapped.get("active_character_before")
        or "unknown"
    )


def row_total_damage(row: Any) -> float:
    mapped = row_mapping(row)
    if mapped.get("total_action_damage") is not None:
        return row_float(mapped, "total_action_damage")
    return row_float(mapped, "damage")


def row_float(row: Any, key: str) -> float:
    mapped = row_mapping(row)
    return _float(mapped.get(key, 0.0))


def event_identity(collection_name: str, event: dict[str, Any]) -> tuple[Any, ...]:
    if event.get("event_id"):
        return ("event_id", event["event_id"])
    if event.get("id"):
        return ("id", event["id"], event.get("source_action_id"), event.get("damage"))
    stable_fields = (
        "scheduled_effect_instance_id",
        "scheduled_effect_id",
        "payload_action_id",
        "source_action_id",
        "source_character_id",
        "response_id",
        "combat_time",
        "trigger_index",
        "scheduled_effect_local_trigger_index",
        "damage",
    )
    stable_key = tuple(event.get(field) for field in stable_fields)
    if any(value is not None for value in stable_key):
        return ("stable",) + stable_key
    return ("object", collection_name, id(event))


def assert_total_close(actual: float, expected: float, label: str, tolerance: float = FLOAT_TOLERANCE) -> None:
    if abs(actual - expected) > tolerance:
        raise DamageAttributionError(
            f"{label} mismatch: actual={actual!r} expected={expected!r} delta={actual - expected!r}"
        )


def character_label(character_id: str) -> str:
    labels = {
        "aemeath": "Aemeath",
        "mornye": "Mornye",
        "lynae": "Lynae",
        "dummy_sub_dps": "Dummy Sub DPS",
    }
    return labels.get(character_id, character_id or "Unknown")


def _role_label(role: str) -> str:
    labels = {
        "scheduled_damage": "scheduled damage",
        "tune_response_damage": "Tune Break response damage",
        "generated_mechanic_damage": "generated mechanic event damage",
    }
    return labels.get(role, role.replace("_", " "))


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
