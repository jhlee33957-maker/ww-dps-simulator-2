from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from rl.damage_attribution import (
    damage_by_character_and_source as event_aware_damage_by_character_and_source,
    effective_damage_role_breakdown as event_aware_effective_damage_role_breakdown,
)


REPORT_GENERATION_VERSION = "generated_damage_reporting_v3_event_source_attribution"
GENERATED_DAMAGE_FIELDS = (
    "generated_mechanic_damage",
    "aemeath_forte_generated_damage",
    "aemeath_seraphic_duet_followup_damage",
    "aemeath_seraphic_duet_followup_variant",
    "aemeath_seraphic_duet_followup_repeat_count",
)
GENERATED_DAMAGE_SUMMARY_KEYS = (
    "generated_mechanic_damage_total",
    "generated_mechanic_damage_action_count",
    "generated_mechanic_damage_share_of_total",
    "aemeath_forte_generated_damage_total",
    "aemeath_seraphic_duet_followup_damage_total",
    "aemeath_seraphic_duet_followup_normal_count",
    "aemeath_seraphic_duet_followup_enhanced_count",
    "damage_by_hit_formula_type",
    "damage_by_generated_mechanic_source",
    "damage_by_character_and_source",
)
NORMAL_VARIANTS = {"normal", "\u5f3a\u5316E-\u9707\u8c10", "Seraphic Duet Tune Rupture Follow-up"}
ENHANCED_VARIANTS = {
    "enhanced",
    "\u5f3a\u5316E-\u9707\u8c10\u589e\u5e45",
    "Seraphic Duet Tune Rupture Enhanced Follow-up",
}


def build_generated_damage_summary(
    timeline: Iterable[Any],
    *,
    total_damage: float | None = None,
) -> dict[str, Any]:
    rows = [_row_mapping(row) for row in timeline]
    resolved_total_damage = float(total_damage or 0.0)
    if resolved_total_damage <= 0.0:
        resolved_total_damage = sum(_float(row, "total_action_damage") for row in rows)

    timeline_has_generated_fields = _timeline_has_generated_damage_fields(rows)
    generated_total = sum(_float(row, "generated_mechanic_damage") for row in rows)
    generated_action_count = sum(1 for row in rows if _float(row, "generated_mechanic_damage") > 0.0)
    generated_hit_count = sum(_generated_hit_count(row) for row in rows)
    direct_damage_total = sum(_direct_damage(row) for row in rows)

    aemeath_forte_total = sum(_float(row, "aemeath_forte_generated_damage") for row in rows)
    followup_rows = [row for row in rows if _is_followup_row(row)]
    followup_total = sum(_float(row, "aemeath_seraphic_duet_followup_damage") for row in followup_rows)
    followup_count = len(followup_rows)
    normal_rows = [row for row in followup_rows if _followup_variant(row) == "normal"]
    enhanced_rows = [row for row in followup_rows if _followup_variant(row) == "enhanced"]
    normal_total = sum(_float(row, "aemeath_seraphic_duet_followup_damage") for row in normal_rows)
    enhanced_total = sum(_float(row, "aemeath_seraphic_duet_followup_damage") for row in enhanced_rows)
    repeat_count_total = sum(_int(row, "aemeath_seraphic_duet_followup_repeat_count") for row in followup_rows)
    multipliers = sorted(
        {
            round(_float(row, "aemeath_seraphic_duet_followup_multiplier"), 10)
            for row in followup_rows
            if _float(row, "aemeath_seraphic_duet_followup_multiplier") > 0.0
        }
    )

    interfered_rows = [row for row in followup_rows if _row_has_generated_interfered_amp(row)]
    interfered_hit_count = sum(_generated_interfered_hit_count(row) for row in followup_rows)
    interfered_missing_count = sum(1 for row in followup_rows if not _row_has_generated_interfered_amp(row))
    direct_damage_by_category = _direct_damage_by_category(rows)

    summary = {
        "report_generation_version": REPORT_GENERATION_VERSION,
        "timeline_schema_has_generated_damage_fields": timeline_has_generated_fields,
        "summary_schema_has_generated_damage_fields": True,
        "generated_damage_reporting_status": _generated_damage_reporting_status(
            timeline_has_generated_fields,
            generated_total,
        ),
        "generated_mechanic_damage_total": generated_total,
        "generated_mechanic_damage_action_count": generated_action_count,
        "generated_mechanic_damage_share_of_total": _share(generated_total, resolved_total_damage),
        "direct_damage_share_of_total": _share(direct_damage_total, resolved_total_damage),
        "aemeath_forte_generated_damage_total": aemeath_forte_total,
        "aemeath_forte_generated_damage_share_of_total": _share(aemeath_forte_total, resolved_total_damage),
        "aemeath_seraphic_duet_followup_count": followup_count,
        "aemeath_seraphic_duet_followup_damage_total": followup_total,
        "aemeath_seraphic_duet_followup_damage_share_of_total": _share(followup_total, resolved_total_damage),
        "aemeath_seraphic_duet_followup_normal_count": len(normal_rows),
        "aemeath_seraphic_duet_followup_enhanced_count": len(enhanced_rows),
        "aemeath_seraphic_duet_followup_normal_damage_total": normal_total,
        "aemeath_seraphic_duet_followup_enhanced_damage_total": enhanced_total,
        "aemeath_seraphic_duet_followup_total_repeat_count": repeat_count_total,
        "aemeath_seraphic_duet_followup_average_damage": (
            followup_total / followup_count if followup_count else 0.0
        ),
        "aemeath_seraphic_duet_followup_source_multipliers": multipliers,
        "aemeath_seraphic_duet_followup_source_multiplier_note": (
            "Source multiplier remains 1.0935 when present; 1.531 / 1.5309 is not hardcoded "
            "as the coefficient."
        ),
        "aemeath_forte_interfered_amp_damage_events": len(interfered_rows),
        "aemeath_forte_interfered_amp_damage_total": sum(
            _float(row, "aemeath_seraphic_duet_followup_damage") for row in interfered_rows
        ),
        "aemeath_forte_interfered_amp_applied_count": interfered_hit_count,
        "aemeath_forte_interfered_amp_missing_count": interfered_missing_count,
        "aemeath_forte_interfered_amp_note": (
            "Interfered Marker is reported as damage-taken amp and is not part of the 1.0935 source multiplier."
        ),
        "damage_by_action_damage_category": _damage_by_action_damage_category(rows),
        "damage_by_hit_formula_type": _damage_by_hit_formula_type(rows),
        "damage_by_generated_mechanic_source": _damage_by_generated_mechanic_source(rows),
        "damage_by_character_and_source_schema_version": "event_source_attribution_v2",
        "damage_by_character_and_source": _damage_by_character_and_source(rows, resolved_total_damage),
        "legacy_damage_by_source_action_category": _legacy_damage_by_source_action_category(rows),
        "legacy_damage_by_source_action_category_note": (
            "Backward-compatible source action category totals include generated mechanic damage attached to "
            "the source action."
        ),
        "direct_damage_by_category": direct_damage_by_category,
        "direct_damage_by_damage_bonus_category": _direct_damage_by_damage_bonus_category(rows),
        "generated_damage_by_source_action_category": _generated_damage_by_source_action_category(rows),
        "effective_damage_role_breakdown": _effective_damage_role_breakdown(rows, resolved_total_damage),
        "basic_attack_direct_damage_share_of_total": _share(
            direct_damage_by_category.get("basic_attack", 0.0),
            resolved_total_damage,
        ),
        "resonance_liberation_direct_damage_share_of_total": _share(
            direct_damage_by_category.get("resonance_liberation", 0.0),
            resolved_total_damage,
        ),
    }
    if generated_hit_count > 0:
        summary["generated_mechanic_damage_hit_count"] = generated_hit_count
    if repeat_count_total > 0:
        summary["aemeath_seraphic_duet_followup_average_damage_per_hit"] = followup_total / repeat_count_total
    return summary


def add_generated_damage_summary(
    payload: dict[str, Any],
    timeline: Iterable[Any],
    *,
    total_damage: float | None = None,
) -> dict[str, Any]:
    updated = dict(payload)
    updated.update(build_generated_damage_summary(timeline, total_damage=total_damage))
    return updated


def _row_mapping(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return row
    if hasattr(row, "model_dump"):
        return row.model_dump()
    return dict(getattr(row, "__dict__", {}))


def _timeline_has_generated_damage_fields(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return True
    return any(any(field in row for field in GENERATED_DAMAGE_FIELDS) for row in rows)


def _generated_damage_reporting_status(timeline_has_generated_fields: bool, generated_total: float) -> str:
    if not timeline_has_generated_fields:
        return "no_generated_damage_fields_in_timeline"
    if generated_total <= 0.0:
        return "zero_generated_damage"
    return "ok"


def _float(row: dict[str, Any], key: str) -> float:
    try:
        return float(row.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _int(row: dict[str, Any], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _bool(row: dict[str, Any], key: str) -> bool:
    value = row.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _share(amount: float, total: float) -> float:
    return amount / total if total > 0.0 else 0.0


def _hit_details(row: dict[str, Any]) -> list[dict[str, Any]]:
    details = row.get("hit_details") or []
    return [detail for detail in details if isinstance(detail, dict)]


def _generated_hits(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [hit for hit in _hit_details(row) if hit.get("is_generated_mechanic_damage")]


def _generated_hit_count(row: dict[str, Any]) -> int:
    logged = _int(row, "generated_mechanic_hit_count")
    return logged if logged > 0 else len(_generated_hits(row))


def _is_followup_row(row: dict[str, Any]) -> bool:
    return _bool(row, "aemeath_seraphic_duet_followup_triggered") or (
        _float(row, "aemeath_seraphic_duet_followup_damage") > 0.0
    )


def _followup_variant(row: dict[str, Any]) -> str:
    variant = str(row.get("aemeath_seraphic_duet_followup_variant") or "").strip()
    if variant in NORMAL_VARIANTS:
        return "normal"
    if variant in ENHANCED_VARIANTS:
        return "enhanced"
    repeat_count = _int(row, "aemeath_seraphic_duet_followup_repeat_count")
    if repeat_count == 5:
        return "normal"
    if repeat_count == 10:
        return "enhanced"
    return variant or "unknown"


def _row_has_generated_interfered_amp(row: dict[str, Any]) -> bool:
    if any(_hit_amp(hit) > 0.0 for hit in _generated_hits(row)):
        return True
    return _is_followup_row(row) and _float(row, "interfered_marker_damage_taken_amp") > 0.0


def _generated_interfered_hit_count(row: dict[str, Any]) -> int:
    count = sum(1 for hit in _generated_hits(row) if _hit_amp(hit) > 0.0)
    if count > 0:
        return count
    return _generated_hit_count(row) if _row_has_generated_interfered_amp(row) else 0


def _hit_amp(hit: dict[str, Any]) -> float:
    return max(
        _float(hit, "effective_damage_taken_amp"),
        _float(hit, "applied_damage_taken_amp"),
    )


def _damage_by_hit_formula_type(rows: list[dict[str, Any]]) -> dict[str, float]:
    damage_by_formula: Counter[str] = Counter({"normal": 0.0, "tune_break": 0.0, "tune_response": 0.0})
    for row in rows:
        damage_by_formula["normal"] += _float(row, "normal_damage")
        damage_by_formula["tune_break"] += _float(row, "tune_break_damage")
        damage_by_formula["tune_response"] += _float(row, "tune_response_damage")
        generated_from_hits = 0.0
        for hit in _generated_hits(row):
            damage = _float(hit, "damage")
            generated_from_hits += damage
            formula_type = str(hit.get("formula_type") or hit.get("damage_category") or "generated_mechanic_damage")
            damage_by_formula[formula_type] += damage
        generated_total = _float(row, "generated_mechanic_damage")
        residual = max(0.0, generated_total - generated_from_hits)
        if residual > 0.0:
            damage_by_formula["generated_mechanic_damage"] += residual
    damage_by_formula.setdefault("generated_mechanic_damage", 0.0)
    return dict(damage_by_formula)


def _damage_by_generated_mechanic_source(rows: list[dict[str, Any]]) -> dict[str, float]:
    damage_by_source: Counter[str] = Counter({"aemeath_forte": 0.0, "other": 0.0})
    for row in rows:
        generated_total = _float(row, "generated_mechanic_damage")
        if generated_total <= 0.0:
            continue
        aemeath_total = _float(row, "aemeath_forte_generated_damage")
        if aemeath_total > 0.0:
            damage_by_source["aemeath_forte"] += aemeath_total
            residual = max(0.0, generated_total - aemeath_total)
            if residual:
                damage_by_source["other"] += residual
        else:
            damage_by_source["other"] += generated_total
    return dict(damage_by_source)


def _damage_by_character_and_source(rows: list[dict[str, Any]], total_damage: float) -> dict[str, float]:
    return event_aware_damage_by_character_and_source(rows, total_damage=total_damage)


def _damage_by_action_damage_category(rows: list[dict[str, Any]]) -> dict[str, float]:
    damage_by_category: Counter[str] = Counter()
    for row in rows:
        category = str(row.get("damage_bonus_category") or row.get("damage_category") or "other")
        damage_by_category[category] += _float(row, "total_action_damage")
    return dict(damage_by_category)


def _legacy_damage_by_source_action_category(rows: list[dict[str, Any]]) -> dict[str, float]:
    damage_by_category: Counter[str] = Counter()
    for row in rows:
        damage_by_category[_source_action_category(row)] += _float(row, "total_action_damage")
    return dict(damage_by_category)


def _direct_damage_by_category(rows: list[dict[str, Any]]) -> dict[str, float]:
    damage_by_category: Counter[str] = Counter()
    for row in rows:
        damage_by_category[_source_action_category(row)] += _direct_damage(row)
    return dict(damage_by_category)


def _direct_damage_by_damage_bonus_category(rows: list[dict[str, Any]]) -> dict[str, float]:
    damage_by_category: Counter[str] = Counter()
    for row in rows:
        category = str(row.get("damage_bonus_category") or row.get("damage_category") or "other")
        damage_by_category[category] += _direct_damage(row)
    return dict(damage_by_category)


def _generated_damage_by_source_action_category(rows: list[dict[str, Any]]) -> dict[str, float]:
    damage_by_category: Counter[str] = Counter()
    for row in rows:
        damage = _float(row, "generated_mechanic_damage")
        if damage > 0.0:
            damage_by_category[_source_action_category(row)] += damage
    return dict(damage_by_category)


def _effective_damage_role_breakdown(rows: list[dict[str, Any]], total_damage: float) -> dict[str, float]:
    result = event_aware_effective_damage_role_breakdown(rows, total_damage)
    aemeath_forte_total = sum(_float(row, "aemeath_forte_generated_damage") for row in rows)
    result["aemeath_forte_generated_damage"] = aemeath_forte_total
    result["other_generated_mechanic_damage"] = max(0.0, result["generated_mechanic_damage"] - aemeath_forte_total)
    return result


def _source_action_category(row: dict[str, Any]) -> str:
    return str(row.get("damage_category") or "other")


def _direct_damage(row: dict[str, Any]) -> float:
    return max(0.0, _float(row, "total_action_damage") - _float(row, "generated_mechanic_damage"))


def _character_label(character_id: str) -> str:
    labels = {"aemeath": "Aemeath", "mornye": "Mornye", "dummy_sub_dps": "Dummy Sub DPS"}
    return labels.get(character_id, character_id or "Unknown")
