from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from simulator.models import ActionData, CharacterData


DAMAGE_BONUS_CATEGORIES = {
    "basic_attack",
    "heavy_attack",
    "resonance_skill",
    "resonance_liberation",
    "intro",
    "outro",
    "coordinated_attack",
    "other",
}
ELEMENT_KEYS = {"generic", "spectro", "aero", "fusion", "electro", "glacio", "havoc"}
SCALING_STATS = {"atk", "def", "hp", "none", "unresolved"}
COMPONENT_STATS = ("atk", "def", "hp")
DEFAULT_SUPPORT_STATS = {
    "off_tune_buildup_rate": 1.0,
}
LEGACY_CATEGORY_ALIASES = {
    "basic_attack_dmg_bonus": "basic_attack",
    "heavy_attack_dmg_bonus": "heavy_attack",
    "resonance_skill_dmg_bonus": "resonance_skill",
    "resonance_liberation_dmg_bonus": "resonance_liberation",
}
RAW_DAMAGE_TYPE_ALIASES = {
    "普通攻击伤害": "basic_attack",
    "普攻伤害": "basic_attack",
    "重击伤害": "heavy_attack",
    "共鸣技能伤害": "resonance_skill",
    "共鸣解放伤害": "resonance_liberation",
    "变奏伤害": "intro",
    "延奏伤害": "outro",
    "震谐伤害": "other",
}

LEGACY_ATTACK_ALIASES = {
    "character_base_atk": ("atk", "character_base"),
    "weapon_base_atk": ("atk", "weapon_base"),
    "static_atk_percent": ("atk", "percent"),
    "static_flat_atk": ("atk", "flat"),
    "runtime_atk_percent_bonus": ("atk", "runtime_percent"),
    "runtime_flat_atk_bonus": ("atk", "runtime_flat"),
    "runtime_atk_flat_bonus": ("atk", "runtime_flat"),
    "final_attack_reference": ("atk", "final_reference"),
    "final_atk_reference": ("atk", "final_reference"),
    "atk_percent": ("atk", "percent"),
    "flat_atk": ("atk", "flat"),
}
STAT_OVERRIDE_FIELDS = set(LEGACY_ATTACK_ALIASES) | {
    "crit_rate",
    "crit_damage",
    "energy_regen",
    "def.character_base",
    "def.percent",
    "def.flat",
    "def.final_reference",
    "def.runtime_percent",
    "def.runtime_flat",
    "hp.character_base",
    "hp.percent",
    "hp.flat",
    "hp.final_reference",
    "hp.runtime_percent",
    "hp.runtime_flat",
    "character_base_def",
    "static_def_percent",
    "static_flat_def",
    "final_def_reference",
    "runtime_def_percent_bonus",
    "runtime_def_flat_bonus",
    "character_base_hp",
    "static_hp_percent",
    "static_flat_hp",
    "final_hp_reference",
    "runtime_hp_percent_bonus",
    "runtime_hp_flat_bonus",
}
COMBAT_STAT_FIELDS = {"crit_rate", "crit_damage", "energy_regen"}
DEFAULT_ATTACK_REFERENCE_TOLERANCE = 0.01
DEFAULT_REFERENCE_TOLERANCE = DEFAULT_ATTACK_REFERENCE_TOLERANCE


def normalize_damage_bonus_category(value: str | None) -> str:
    if not value:
        return "other"
    normalized = str(value).strip()
    if not normalized or normalized == "-":
        return "other"
    return normalized if normalized in DAMAGE_BONUS_CATEGORIES else "other"


def raw_damage_type_to_damage_bonus_category(raw_damage_type: str | None) -> str:
    if raw_damage_type is None:
        return "other"
    normalized = str(raw_damage_type).strip()
    if not normalized or normalized == "-":
        return "other"
    return RAW_DAMAGE_TYPE_ALIASES.get(normalized, "other")


def normalize_support_stats(support_stats: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized: dict[str, Any] = dict(DEFAULT_SUPPORT_STATS)
    for key, value in (support_stats or {}).items():
        if key == "off_tune_buildup_rate":
            normalized[key] = 1.0 if value is None else float(value)
        else:
            normalized[str(key)] = value
    if normalized.get("off_tune_buildup_rate") is None:
        normalized["off_tune_buildup_rate"] = 1.0
    return normalized


def merge_support_stats(base: dict[str, Any] | None, overlay: dict[str, Any] | None) -> dict[str, Any]:
    merged = normalize_support_stats(base)
    for key, value in (overlay or {}).items():
        merged[str(key)] = 1.0 if key == "off_tune_buildup_rate" and value is None else value
    return normalize_support_stats(merged)


def normalize_scaling_stat(value: str | None, *, default: str = "unresolved") -> str:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    return normalized if normalized in SCALING_STATS else default


def load_build_profiles(data_dir: Path | str = "data") -> dict[str, Any]:
    path = Path(data_dir) / "build_profiles.json"
    if not path.exists():
        return {"schema_version": 1, "profiles": {}}
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def get_available_build_profiles(
    character_id: str,
    build_profiles: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = build_profiles if build_profiles is not None else load_build_profiles()
    return dict((data.get("profiles") or {}).get(character_id, {}))


def parse_build_profile_overrides(values: list[str] | tuple[str, ...] | None) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for raw_value in values or []:
        if ":" not in raw_value:
            raise ValueError(f"Build profile override must use character_id:profile_id, got {raw_value!r}.")
        character_id, profile_id = (part.strip() for part in raw_value.split(":", 1))
        if not character_id or not profile_id:
            raise ValueError(f"Build profile override must use character_id:profile_id, got {raw_value!r}.")
        overrides[character_id] = profile_id
    return overrides


def normalize_damage_bonuses(
    damage_bonuses: dict[str, Any] | None = None,
    *,
    legacy_all: float = 0.0,
    legacy_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = damage_bonuses or {}
    normalized: dict[str, Any] = {
        "all": float(legacy_all),
        "by_category": {},
        "by_element": {},
    }

    if "all" in source:
        normalized["all"] += float(source.get("all") or 0.0)
    for category, value in (source.get("by_category") or {}).items():
        normalized["by_category"][str(category)] = float(value or 0.0)
    for element, value in (source.get("by_element") or {}).items():
        normalized["by_element"][str(element)] = float(value or 0.0)

    fields = legacy_fields or {}
    if not damage_bonuses and legacy_all == 0.0 and fields.get("damage_bonus") is not None:
        normalized["all"] += float(fields.get("damage_bonus") or 0.0)
    if fields.get("elemental_dmg_bonus") is not None:
        normalized["by_element"]["generic"] = normalized["by_element"].get("generic", 0.0) + float(fields["elemental_dmg_bonus"])
    for field_name, category in LEGACY_CATEGORY_ALIASES.items():
        if fields.get(field_name) is not None:
            normalized["by_category"][category] = normalized["by_category"].get(category, 0.0) + float(fields[field_name])

    return normalized


def empty_stat_components() -> dict[str, dict[str, float | None]]:
    return {
        stat: {
            "character_base": 0.0,
            "weapon_base": 0.0,
            "percent": 0.0,
            "flat": 0.0,
            "runtime_percent": 0.0,
            "runtime_flat": 0.0,
            "final_reference": None,
        }
        for stat in COMPONENT_STATS
    }


def calculate_single_stat_component(
    *,
    character_base: float,
    weapon_base: float = 0.0,
    percent: float = 0.0,
    flat: float = 0.0,
    runtime_percent: float = 0.0,
    runtime_flat: float = 0.0,
    final_reference: float | None = None,
) -> dict[str, float | None]:
    base_total = float(character_base) + float(weapon_base)
    static_value = base_total * (1.0 + float(percent)) + float(flat)
    effective_value = static_value + base_total * float(runtime_percent) + float(runtime_flat)
    reference_delta = None
    reference_delta_percent = None
    if final_reference not in (None, 0):
        reference = float(final_reference)
        reference_delta = static_value - reference
        reference_delta_percent = reference_delta / reference
    return {
        "character_base": float(character_base),
        "weapon_base": float(weapon_base),
        "base_total": base_total,
        "percent": float(percent),
        "flat": float(flat),
        "runtime_percent": float(runtime_percent),
        "runtime_flat": float(runtime_flat),
        "static_value": static_value,
        "effective_value": effective_value,
        "final_reference": None if final_reference is None else float(final_reference),
        "reference_delta": reference_delta,
        "reference_delta_percent": reference_delta_percent,
    }


def calculate_scaling_stat_components(
    components: dict[str, Any],
    runtime_bonuses: dict[str, Any] | None = None,
) -> dict[str, dict[str, float | None]]:
    normalized = normalize_stat_components(components, runtime_bonuses=runtime_bonuses)
    return {
        stat: calculate_single_stat_component(
            character_base=float(values.get("character_base") or 0.0),
            weapon_base=float(values.get("weapon_base") or 0.0),
            percent=float(values.get("percent") or 0.0),
            flat=float(values.get("flat") or 0.0),
            runtime_percent=float(values.get("runtime_percent") or 0.0),
            runtime_flat=float(values.get("runtime_flat") or 0.0),
            final_reference=values.get("final_reference"),
        )
        for stat, values in normalized.items()
    }


def calculate_attack_components(
    *,
    character_base_atk: float,
    weapon_base_atk: float,
    static_atk_percent: float = 0.0,
    static_flat_atk: float = 0.0,
    runtime_atk_percent_bonus: float = 0.0,
    runtime_flat_atk_bonus: float = 0.0,
    final_attack_reference: float | None = None,
) -> dict[str, float | None]:
    calculated = calculate_scaling_stat_components(
        {
            "atk": {
                "character_base": character_base_atk,
                "weapon_base": weapon_base_atk,
                "percent": static_atk_percent,
                "flat": static_flat_atk,
                "runtime_percent": runtime_atk_percent_bonus,
                "runtime_flat": runtime_flat_atk_bonus,
                "final_reference": final_attack_reference,
            }
        }
    )["atk"]
    return _legacy_attack_fields(calculated)


def normalize_stat_components(
    components: dict[str, Any] | None,
    *,
    runtime_bonuses: dict[str, Any] | None = None,
) -> dict[str, dict[str, float | None]]:
    normalized = empty_stat_components()
    source = components or {}

    for stat in COMPONENT_STATS:
        stat_source = source.get(stat) if isinstance(source.get(stat), dict) else {}
        for field in ("character_base", "weapon_base", "percent", "flat", "final_reference"):
            if field in stat_source:
                normalized[stat][field] = stat_source.get(field)
        runtime_source = (runtime_bonuses or {}).get(stat) if isinstance((runtime_bonuses or {}).get(stat), dict) else {}
        for field in ("percent", "flat"):
            runtime_key = f"runtime_{field}"
            if runtime_key in stat_source:
                normalized[stat][runtime_key] = stat_source.get(runtime_key)
            if field in runtime_source:
                normalized[stat][runtime_key] = runtime_source.get(field)

    for old_name, (stat, field) in LEGACY_ATTACK_ALIASES.items():
        if old_name not in source:
            continue
        target = "final_reference" if field == "final_reference" else field
        if field == "runtime_percent":
            target = "runtime_percent"
        elif field == "runtime_flat":
            target = "runtime_flat"
        normalized[stat][target] = source.get(old_name)

    flat_aliases = {
        "character_base_def": ("def", "character_base"),
        "weapon_base_def": ("def", "weapon_base"),
        "static_def_percent": ("def", "percent"),
        "static_flat_def": ("def", "flat"),
        "runtime_def_percent_bonus": ("def", "runtime_percent"),
        "runtime_def_flat_bonus": ("def", "runtime_flat"),
        "final_def_reference": ("def", "final_reference"),
        "character_base_hp": ("hp", "character_base"),
        "weapon_base_hp": ("hp", "weapon_base"),
        "static_hp_percent": ("hp", "percent"),
        "static_flat_hp": ("hp", "flat"),
        "runtime_hp_percent_bonus": ("hp", "runtime_percent"),
        "runtime_hp_flat_bonus": ("hp", "runtime_flat"),
        "final_hp_reference": ("hp", "final_reference"),
    }
    for old_name, (stat, field) in flat_aliases.items():
        if old_name in source:
            normalized[stat][field] = source.get(old_name)

    return normalized


def apply_scaling_components_to_character(
    character: CharacterData,
    components: dict[str, Any],
    *,
    runtime_bonuses: dict[str, Any] | None = None,
    tolerance: float = DEFAULT_REFERENCE_TOLERANCE,
) -> CharacterData:
    calculated = calculate_scaling_stat_components(components, runtime_bonuses)
    character.stat_components = normalize_stat_components(components, runtime_bonuses=runtime_bonuses)
    character.runtime_bonuses = runtime_bonuses or {}
    for stat, values in calculated.items():
        _apply_calculated_stat(character, stat, values)
        if values["reference_delta_percent"] is not None and abs(float(values["reference_delta_percent"])) > tolerance:
            label = stat.upper()
            warning = (
                f"Calculated {label} does not match final_{stat}_reference. "
                f"Check base {label}, {label}%, and flat {label} inputs."
            )
            if warning not in character.profile_warnings:
                character.profile_warnings.append(warning)
    character.attack = character.effective_atk
    character.atk_percent = character.static_atk_percent
    character.flat_atk = character.static_flat_atk
    return character


def apply_attack_components_to_character(
    character: CharacterData,
    components: dict[str, Any],
    *,
    tolerance: float = DEFAULT_ATTACK_REFERENCE_TOLERANCE,
) -> CharacterData:
    return apply_scaling_components_to_character(character, {"atk": _legacy_to_atk_components(components)}, tolerance=tolerance)


def character_stat_components_from_legacy(character: CharacterData) -> dict[str, Any]:
    return {
        "atk": {
            "character_base": character.character_base_atk,
            "weapon_base": character.weapon_base_atk,
            "percent": character.static_atk_percent if character.static_atk_percent else character.atk_percent,
            "flat": character.static_flat_atk if character.static_flat_atk else character.flat_atk,
            "runtime_percent": character.runtime_atk_percent_bonus,
            "runtime_flat": character.runtime_flat_atk_bonus or character.runtime_atk_flat_bonus,
            "final_reference": character.final_attack_reference or character.final_atk_reference,
        },
        "def": {
            "character_base": character.character_base_def,
            "weapon_base": character.weapon_base_def,
            "percent": character.static_def_percent,
            "flat": character.static_flat_def,
            "runtime_percent": character.runtime_def_percent_bonus,
            "runtime_flat": character.runtime_def_flat_bonus,
            "final_reference": character.final_def_reference,
        },
        "hp": {
            "character_base": character.character_base_hp,
            "weapon_base": character.weapon_base_hp,
            "percent": character.static_hp_percent,
            "flat": character.static_flat_hp,
            "runtime_percent": character.runtime_hp_percent_bonus,
            "runtime_flat": character.runtime_hp_flat_bonus,
            "final_reference": character.final_hp_reference,
        },
    }


def parse_stat_overrides(values: list[str] | tuple[str, ...] | None) -> dict[str, dict[str, float]]:
    overrides: dict[str, dict[str, float]] = {}
    for raw_value in values or []:
        parts = [part.strip() for part in raw_value.split(":")]
        if len(parts) != 3 or not all(parts):
            raise ValueError(f"Stat override must use character_id:field:value, got {raw_value!r}.")
        character_id, field_name, value_text = parts
        if field_name not in STAT_OVERRIDE_FIELDS:
            raise ValueError(f"Unknown stat override field {field_name!r}. Allowed fields: {sorted(STAT_OVERRIDE_FIELDS)}.")
        try:
            value = float(value_text)
        except ValueError as exc:
            raise ValueError(f"Stat override value must be numeric, got {raw_value!r}.") from exc
        overrides.setdefault(character_id, {})[field_name] = value
    return overrides


def merge_damage_bonuses(base: dict[str, Any], overlay: dict[str, Any] | None) -> dict[str, Any]:
    merged = normalize_damage_bonuses(base)
    extra = normalize_damage_bonuses(overlay)
    merged["all"] += float(extra.get("all", 0.0))
    for category, value in (extra.get("by_category") or {}).items():
        merged["by_category"][category] = merged["by_category"].get(category, 0.0) + float(value)
    for element, value in (extra.get("by_element") or {}).items():
        merged["by_element"][element] = merged["by_element"].get(element, 0.0) + float(value)
    return merged


def resolve_party_build_profiles(
    party_preset: dict[str, Any] | None = None,
    *,
    cli_overrides: dict[str, str] | None = None,
    ui_overrides: dict[str, str] | None = None,
    selected_character_ids: list[str] | tuple[str, ...] | None = None,
    build_profiles: dict[str, Any] | None = None,
) -> dict[str, str]:
    data = build_profiles if build_profiles is not None else load_build_profiles()
    profiles = data.get("profiles") or {}
    resolved: dict[str, str] = {}

    for character_id, profile_id in (party_preset or {}).get("build_profiles", {}).items():
        _require_profile(character_id, profile_id, profiles)
        resolved[character_id] = profile_id

    for character_id in selected_character_ids or []:
        available = profiles.get(character_id, {})
        if character_id not in resolved and "default" in available:
            resolved[character_id] = "default"

    for source in (ui_overrides or {}, cli_overrides or {}):
        for character_id, profile_id in source.items():
            _require_profile(character_id, profile_id, profiles)
            resolved[character_id] = profile_id

    return resolved


def resolve_character_build_stats(
    character_data: CharacterData,
    profile_id: str | None = None,
    build_profiles: dict[str, Any] | None = None,
    stat_overrides: dict[str, float] | None = None,
) -> CharacterData:
    data = build_profiles if build_profiles is not None else load_build_profiles()
    profiles = (data.get("profiles") or {}).get(character_data.id, {})
    if profile_id is None:
        profile_id = "default" if "default" in profiles else None
    if profile_id is None:
        effective = character_data.model_copy(deep=True)
        effective.energy_regen = effective.energy_regen or 1.0
        effective.support_stats = normalize_support_stats(effective.support_stats)
        effective.damage_bonuses = normalize_damage_bonuses({}, legacy_all=effective.dmg_bonus)
        effective.profile_completeness_status = "fallback_character_stats"
        effective.implementation_status = effective.implementation_status or "character_data_fallback"
        apply_scaling_components_to_character(effective, character_stat_components_from_legacy(effective))
        return effective
    _require_profile(character_data.id, profile_id, data.get("profiles") or {})

    effective = character_data.model_copy(deep=True)
    effective.energy_regen = effective.energy_regen or 1.0
    effective.support_stats = normalize_support_stats(effective.support_stats)
    effective.damage_bonuses = normalize_damage_bonuses(
        effective.damage_bonuses,
        legacy_all=effective.dmg_bonus,
        legacy_fields=effective.model_dump(mode="json"),
    )
    components = character_stat_components_from_legacy(effective)
    effective.profile_warnings = []

    for resolved_id, profile in _profile_lineage(character_data.id, profile_id, profiles):
        _apply_profile_aliases_to_components(profile, components, effective.profile_warnings)
        if profile.get("stat_components") and not profile.get("inherits_from_character_stats", False):
            effective.damage_bonuses = normalize_damage_bonuses({})
        _merge_components(components, profile.get("stat_components") or {})
        _merge_runtime_bonuses(components, profile.get("runtime_bonuses") or {})
        for stat_name, stat_value in (profile.get("stat_overrides") or {}).items():
            _apply_stat_override(effective, stat_name, stat_value)
            _apply_override_to_components(components, stat_name, stat_value)
        for stat_name, stat_value in (profile.get("combat_stats") or {}).items():
            if stat_name in COMBAT_STAT_FIELDS and stat_value is not None:
                setattr(effective, stat_name, float(stat_value))
        effective.damage_bonuses = merge_damage_bonuses(effective.damage_bonuses, profile.get("damage_bonuses"))
        if profile.get("damage_bonus") is not None and not (profile.get("damage_bonuses") or {}).get("all"):
            effective.damage_bonuses = merge_damage_bonuses(effective.damage_bonuses, {"all": profile.get("damage_bonus")})
        if profile.get("echo_sets") is not None:
            effective.echo_sets = dict(profile.get("echo_sets") or {})
        if profile.get("weapon") is not None:
            effective.weapon = dict(profile.get("weapon") or {})
        effective.support_stats = merge_support_stats(effective.support_stats, profile.get("support_stats"))
        effective.build_profile_id = resolved_id
        effective.build_profile_display_name = profile.get("display_name", resolved_id)
        effective.build_profile_description = profile.get("description")
        effective.implementation_status = profile.get("implementation_status", effective.implementation_status)
        if profile.get("default_scaling_stat"):
            effective.default_scaling_stat = normalize_scaling_stat(profile.get("default_scaling_stat"), default="atk")

    for stat_name, stat_value in (stat_overrides or {}).items():
        if stat_name in COMBAT_STAT_FIELDS:
            setattr(effective, stat_name, float(stat_value))
        elif stat_name in STAT_OVERRIDE_FIELDS:
            _apply_override_to_components(components, stat_name, stat_value)
        else:
            raise ValueError(f"Unknown stat override {stat_name!r} for {character_data.id}.")

    effective.energy_regen = effective.energy_regen or 1.0
    effective.support_stats = normalize_support_stats(effective.support_stats)
    effective.missing_required_fields = profile_missing_required_fields(
        profiles.get(profile_id, {}),
        effective.damage_bonuses,
    )
    if effective.implementation_status == "user_supplied_required":
        effective.profile_completeness_status = (
            "user_supplied_complete" if not effective.missing_required_fields else "user_supplied_required"
        )
    elif effective.implementation_status == "user_supplied_complete":
        effective.profile_completeness_status = "user_supplied_complete"
    elif effective.implementation_status:
        effective.profile_completeness_status = effective.implementation_status
    else:
        effective.profile_completeness_status = "test_assumption"
        effective.implementation_status = "test_assumption"
    apply_scaling_components_to_character(
        effective,
        components,
        tolerance=float((data.get("reference_tolerance") or data.get("attack_reference_tolerance") or DEFAULT_REFERENCE_TOLERANCE)),
    )

    return effective


def action_damage_bonus_category(action: ActionData) -> str:
    explicit = normalize_damage_bonus_category(getattr(action, "damage_bonus_category", None))
    if explicit != "other":
        return explicit
    tags = set(action.tags or [])
    for tag in ("intro", "outro", "coordinated_attack"):
        if tag in tags:
            return tag
    return normalize_damage_bonus_category(getattr(action, "action_type", None))


def action_damage_element(action: ActionData, character: CharacterData | None = None) -> str:
    explicit = getattr(action, "damage_element", None)
    if explicit:
        return str(explicit).strip().lower()
    for tag in action.tags or []:
        if tag in ELEMENT_KEYS:
            return tag
    for attr_name in ("damage_attribute", "element"):
        if character is not None:
            value = getattr(character, attr_name, None)
            if value:
                return str(value).strip().lower()
    return "generic"


def action_has_normal_damage(action: ActionData) -> bool:
    if action.damage_multiplier > 0.0:
        return True
    return any(hit.damage_category == "normal" and hit.damage_multiplier > 0.0 for hit in action.effective_hits())


def action_scaling_stat(action: ActionData, character: CharacterData | None = None) -> str:
    explicit = normalize_scaling_stat(getattr(action, "scaling_stat", None), default="")
    if explicit:
        return explicit
    if not action_has_normal_damage(action):
        return "none"
    return normalize_scaling_stat(getattr(character, "default_scaling_stat", None), default="atk")


def scaling_value_for_action(stats: dict[str, Any], action: ActionData, character: CharacterData | None = None) -> tuple[str, float]:
    scaling_stat = action_scaling_stat(action, character)
    if scaling_stat == "unresolved":
        raise ValueError(f"Action {action.id!r} has unresolved scaling_stat.")
    if scaling_stat == "none":
        return scaling_stat, 0.0
    return scaling_stat, float(stats.get(f"effective_{scaling_stat}", stats.get("effective_attack", 0.0) if scaling_stat == "atk" else 0.0))


def damage_bonus_breakdown(
    character: CharacterData,
    action: ActionData,
    *,
    additive_buff_bonus: float = 0.0,
    additive_element_bonuses: dict[str, float] | None = None,
    echo_set_element_bonuses: dict[str, float] | None = None,
) -> dict[str, Any]:
    bonuses = normalize_damage_bonuses(character.damage_bonuses, legacy_all=0.0 if character.damage_bonuses else character.dmg_bonus)
    category = action_damage_bonus_category(action)
    element = action_damage_element(action, character)
    all_bonus = float(bonuses.get("all", 0.0)) + float(additive_buff_bonus)
    category_bonus = float((bonuses.get("by_category") or {}).get(category, 0.0))
    element_bonuses = bonuses.get("by_element") or {}
    runtime_element_bonuses = additive_element_bonuses or {}
    echo_element_bonuses = echo_set_element_bonuses or {}
    element_bonus = float(element_bonuses.get(element, element_bonuses.get("generic", 0.0) if element == "generic" else 0.0))
    runtime_element_damage_bonus = float(
        runtime_element_bonuses.get(
            element,
            runtime_element_bonuses.get("generic", 0.0) if element == "generic" else 0.0,
        )
    )
    echo_set_damage_bonus = float(
        echo_element_bonuses.get(
            element,
            echo_element_bonuses.get("generic", 0.0) if element == "generic" else 0.0,
        )
    )
    element_bonus += runtime_element_damage_bonus
    return {
        "damage_category": category,
        "damage_bonus_category": category,
        "damage_element": element,
        "raw_skill_category": getattr(action, "raw_skill_category", None),
        "raw_damage_type": getattr(action, "raw_damage_type", None),
        "all_dmg_bonus": all_bonus,
        "category_dmg_bonus": category_bonus,
        "element_dmg_bonus": element_bonus,
        "runtime_element_damage_bonus": runtime_element_damage_bonus,
        "echo_set_damage_bonus": echo_set_damage_bonus,
        "effective_damage_bonus": all_bonus + category_bonus + element_bonus,
        "build_profile_id": character.build_profile_id,
    }


def stat_component_log_fields(source: CharacterData | dict[str, Any]) -> dict[str, Any]:
    get = source.get if isinstance(source, dict) else lambda name, default=None: getattr(source, name, default)
    fields: dict[str, Any] = {}
    for stat in COMPONENT_STATS:
        fields[f"character_base_{stat}"] = get(f"character_base_{stat}", 0.0)
        fields[f"weapon_base_{stat}"] = get(f"weapon_base_{stat}", 0.0)
        fields[f"base_{stat}_total"] = get(f"base_{stat}_total", 0.0)
        fields[f"static_{stat}_percent"] = get(f"static_{stat}_percent", 0.0)
        fields[f"static_flat_{stat}"] = get(f"static_flat_{stat}", 0.0)
        fields[f"runtime_{stat}_percent_bonus"] = get(f"runtime_{stat}_percent_bonus", 0.0)
        fields[f"runtime_{stat}_flat_bonus"] = get(f"runtime_{stat}_flat_bonus", 0.0)
        fields[f"static_{stat}"] = get(f"static_{stat}", 0.0)
        fields[f"effective_{stat}"] = get(f"effective_{stat}", 0.0)
        fields[f"final_{stat}_reference"] = get(f"final_{stat}_reference", None)
        fields[f"{stat}_reference_delta"] = get(f"{stat}_reference_delta", None)
        fields[f"{stat}_reference_delta_percent"] = get(f"{stat}_reference_delta_percent", None)
    fields.update(
        {
            "base_attack_total": fields["base_atk_total"],
            "static_attack": fields["static_atk"],
            "effective_attack": fields["effective_atk"],
            "final_attack_reference": fields["final_atk_reference"],
            "attack_reference_delta": fields["atk_reference_delta"],
            "attack_reference_delta_percent": fields["atk_reference_delta_percent"],
            "runtime_flat_atk_bonus": fields["runtime_atk_flat_bonus"],
        }
    )
    return fields


def support_stat_log_fields(source: CharacterData | dict[str, Any]) -> dict[str, Any]:
    get = source.get if isinstance(source, dict) else lambda name, default=None: getattr(source, name, default)
    support_stats = get("support_stats", {}) or {}
    base_off_tune = get("base_off_tune_buildup_rate", None)
    if base_off_tune is None:
        base_off_tune = support_stats.get("off_tune_buildup_rate", 1.0)
    runtime_bonus = float(get("runtime_off_tune_buildup_rate_bonus", 0.0) or 0.0)
    current = get("current_off_tune_buildup_rate", None)
    if current is None:
        current = float(base_off_tune or 1.0) + runtime_bonus
    return {
        "base_off_tune_buildup_rate": float(base_off_tune or 1.0),
        "runtime_off_tune_buildup_rate_bonus": runtime_bonus,
        "current_off_tune_buildup_rate": float(current or 1.0),
        "syntony_field_off_tune_bonus_active": bool(get("syntony_field_off_tune_bonus_active", False)),
        "syntony_field_off_tune_bonus_value": float(get("syntony_field_off_tune_bonus_value", 0.0) or 0.0),
        "c2_off_tune_bonus_active": bool(get("c2_off_tune_bonus_active", False)),
        "mornye_constellation": int(get("mornye_constellation", 0) or 0),
        "mornye_heal_event_mode": get("mornye_heal_event_mode", None),
    }


def effective_build_stats_summary(
    characters: dict[str, CharacterData],
    action_scaling_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for character_id, character in characters.items():
        stat_fields = stat_component_log_fields(character)
        summary[character_id] = {
            "build_profile_id": character.build_profile_id,
            "display_name": character.build_profile_display_name,
            "implementation_status": character.implementation_status,
            "profile_completeness_status": character.profile_completeness_status,
            "missing_required_fields": character.missing_required_fields,
            "profile_warnings": character.profile_warnings,
            "stat_components": character.stat_components,
            "runtime_bonuses": character.runtime_bonuses,
            "energy_regen": character.energy_regen,
            "crit_rate": character.crit_rate,
            "crit_damage": character.crit_damage,
            "damage_bonuses": character.damage_bonuses,
            "echo_sets": character.echo_sets,
            "weapon": character.weapon,
            "support_stats": normalize_support_stats(character.support_stats),
            **stat_fields,
            **support_stat_log_fields(character),
        }
        if action_scaling_summary and character_id in action_scaling_summary:
            summary[character_id].update(action_scaling_summary[character_id])
    return summary


def build_action_scaling_summary(
    actions: Iterable[ActionData],
    selected_character_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    selected = set(selected_character_ids or [])
    by_character: dict[str, Any] = {}
    for action in actions:
        if action.character_id is None:
            continue
        if selected and action.character_id not in selected:
            continue
        character_summary = by_character.setdefault(
            action.character_id,
            {
                "scaling_stat_distribution": {},
                "unresolved_scaling_actions": [],
                "actions_requiring_def_stats": [],
                "actions_requiring_hp_stats": [],
                "actions_requiring_atk_stats": [],
                "missing_scaling_stat_actions": [],
            },
        )
        explicit_scaling = getattr(action, "scaling_stat", None)
        scaling_stat = action_scaling_stat(action)
        character_summary["scaling_stat_distribution"][scaling_stat] = (
            character_summary["scaling_stat_distribution"].get(scaling_stat, 0) + 1
        )
        if action_has_normal_damage(action) and not explicit_scaling:
            character_summary["missing_scaling_stat_actions"].append(action.id)
        if scaling_stat == "unresolved":
            character_summary["unresolved_scaling_actions"].append(action.id)
        elif scaling_stat in {"atk", "def", "hp"} and action_has_normal_damage(action):
            character_summary[f"actions_requiring_{scaling_stat}_stats"].append(action.id)
    return by_character


def profile_missing_required_fields(
    profile: dict[str, Any],
    damage_bonuses: dict[str, Any] | None = None,
    *,
    required_scaling_stats: Iterable[str] | None = None,
) -> list[str]:
    missing: list[str] = []
    stat_components = normalize_stat_components(profile.get("stat_components") or {})
    combat_stats = profile.get("combat_stats") or {}
    profile_damage_bonuses = profile.get("damage_bonuses") or {}
    required_stats = list(required_scaling_stats or profile.get("required_scaling_stats") or ["atk"])
    for stat in required_stats:
        if stat not in {"atk", "def", "hp"}:
            continue
        for field in _required_component_fields_for_stat(stat):
            if stat_components.get(stat, {}).get(field) is None:
                missing.append(f"stat_components.{stat}.{field}")
    for field_name in ("crit_rate", "crit_damage", "energy_regen"):
        if combat_stats.get(field_name) is None:
            missing.append(f"combat_stats.{field_name}")
    for field_path in _required_damage_bonus_fields():
        group, field_name, *rest = field_path.split(".")
        value: Any = None
        if group == "damage_bonuses":
            if field_name == "all":
                value = profile_damage_bonuses.get("all")
            elif field_name == "by_category" and rest:
                value = (profile_damage_bonuses.get("by_category") or {}).get(rest[0])
        if value is None:
            missing.append(field_path)
    return missing


def validate_effective_build_profiles(
    effective_stats_summary: dict[str, Any],
    *,
    allow_test_assumptions: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    for character_id, summary in effective_stats_summary.items():
        implementation_status = summary.get("implementation_status")
        missing = list(summary.get("missing_required_fields") or [])
        required_scaling_stats = _required_scaling_stats_from_summary(summary)
        missing.extend(_missing_required_stat_fields(summary, required_scaling_stats))
        unresolved = summary.get("unresolved_scaling_actions") or []
        profile_label = f"{character_id}:{summary.get('build_profile_id')}"
        if implementation_status == "user_supplied_required":
            if missing:
                errors.append(f"{profile_label} is incomplete; missing fields: {', '.join(sorted(set(missing)))}")
            if unresolved:
                errors.append(f"{profile_label} has unresolved scaling actions: {', '.join(unresolved)}")
        if implementation_status == "test_assumption" or implementation_status == "configurable_test_assumption":
            if allow_test_assumptions:
                warnings.append(
                    f"{profile_label} uses test-assumption stat profiles, not verified real-game stats."
                )
        if unresolved and implementation_status != "user_supplied_required":
            warnings.append(f"{profile_label} has unresolved scaling actions: {', '.join(unresolved)}")
        if summary.get("missing_scaling_stat_actions"):
            warnings.append(
                f"{profile_label} has damage actions missing explicit scaling_stat: "
                f"{', '.join(summary['missing_scaling_stat_actions'])}"
            )
        warnings.extend(summary.get("profile_warnings") or [])
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _profile_lineage(character_id: str, profile_id: str, profiles: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    lineage: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    current_id: str | None = profile_id
    while current_id:
        if current_id in seen:
            raise ValueError(f"Build profile inheritance cycle for {character_id}:{profile_id}.")
        seen.add(current_id)
        profile = profiles[current_id]
        lineage.append((current_id, profile))
        current_id = profile.get("inherits_from")
    return list(reversed(lineage))


def _apply_stat_override(character: CharacterData, stat_name: str, stat_value: Any) -> None:
    if stat_name == "damage_bonus":
        character.damage_bonuses = merge_damage_bonuses(character.damage_bonuses, {"all": float(stat_value)})
        character.damage_bonus = float(stat_value)
        character.dmg_bonus = float(stat_value)
        return
    if stat_name == "elemental_dmg_bonus":
        character.damage_bonuses = merge_damage_bonuses(character.damage_bonuses, {"by_element": {"generic": float(stat_value)}})
        return
    if stat_name in LEGACY_CATEGORY_ALIASES:
        character.damage_bonuses = merge_damage_bonuses(
            character.damage_bonuses,
            {"by_category": {LEGACY_CATEGORY_ALIASES[stat_name]: float(stat_value)}},
        )
        return
    if not hasattr(character, stat_name):
        raise ValueError(f"Unknown build profile stat override {stat_name!r} for {character.id}.")
    setattr(character, stat_name, stat_value)


def _apply_profile_aliases_to_components(
    profile: dict[str, Any],
    components: dict[str, Any],
    warnings: list[str],
) -> None:
    for old_name, (stat, field) in LEGACY_ATTACK_ALIASES.items():
        if old_name not in profile:
            continue
        stat_components = profile.get("stat_components") or {}
        new_value = (stat_components.get(stat) or {}).get(field) if isinstance(stat_components.get(stat), dict) else stat_components.get(old_name)
        if new_value is None:
            _set_component_value(components, stat, field, profile[old_name])
        elif profile[old_name] != new_value:
            warnings.append(f"Build profile has conflicting {old_name} and stat_components.{stat}.{field}; using new schema.")
    if "damage_bonus" in profile and not (profile.get("damage_bonuses") or {}).get("all"):
        warnings.append("Build profile uses legacy damage_bonus; normalized as damage_bonuses.all.")
    elif "damage_bonus" in profile and (profile.get("damage_bonuses") or {}).get("all") != profile["damage_bonus"]:
        warnings.append("Build profile has conflicting damage_bonus and damage_bonuses.all; using damage_bonuses.all.")


def _legacy_to_atk_components(components: dict[str, Any]) -> dict[str, Any]:
    if "atk" in components and isinstance(components["atk"], dict):
        return dict(components["atk"])
    return {
        "character_base": components.get("character_base_atk", components.get("character_base", 0.0)),
        "weapon_base": components.get("weapon_base_atk", components.get("weapon_base", 0.0)),
        "percent": components.get("static_atk_percent", components.get("atk_percent", components.get("percent", 0.0))),
        "flat": components.get("static_flat_atk", components.get("flat_atk", components.get("flat", 0.0))),
        "runtime_percent": components.get("runtime_atk_percent_bonus", components.get("runtime_percent", 0.0)),
        "runtime_flat": components.get("runtime_flat_atk_bonus", components.get("runtime_atk_flat_bonus", components.get("runtime_flat", 0.0))),
        "final_reference": components.get("final_attack_reference", components.get("final_reference")),
    }


def _legacy_attack_fields(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "character_base_atk": values["character_base"],
        "weapon_base_atk": values["weapon_base"],
        "base_attack_total": values["base_total"],
        "static_atk_percent": values["percent"],
        "static_flat_atk": values["flat"],
        "runtime_atk_percent_bonus": values["runtime_percent"],
        "runtime_flat_atk_bonus": values["runtime_flat"],
        "static_attack": values["static_value"],
        "effective_attack": values["effective_value"],
        "final_attack_reference": values["final_reference"],
        "attack_reference_delta": values["reference_delta"],
        "attack_reference_delta_percent": values["reference_delta_percent"],
    }


def _apply_calculated_stat(character: CharacterData, stat: str, values: dict[str, Any]) -> None:
    setattr(character, f"character_base_{stat}", values["character_base"])
    setattr(character, f"weapon_base_{stat}", values["weapon_base"])
    setattr(character, f"base_{stat}_total", values["base_total"])
    setattr(character, f"static_{stat}_percent", values["percent"])
    setattr(character, f"static_flat_{stat}", values["flat"])
    setattr(character, f"runtime_{stat}_percent_bonus", values["runtime_percent"])
    setattr(character, f"runtime_{stat}_flat_bonus", values["runtime_flat"])
    setattr(character, f"static_{stat}", values["static_value"])
    setattr(character, f"effective_{stat}", values["effective_value"])
    setattr(character, f"final_{stat}_reference", values["final_reference"])
    setattr(character, f"{stat}_reference_delta", values["reference_delta"])
    setattr(character, f"{stat}_reference_delta_percent", values["reference_delta_percent"])
    if stat == "atk":
        character.base_attack_total = values["base_total"]
        character.static_attack = values["static_value"]
        character.effective_attack = values["effective_value"]
        character.final_attack_reference = values["final_reference"]
        character.attack_reference_delta = values["reference_delta"]
        character.attack_reference_delta_percent = values["reference_delta_percent"]
        character.runtime_flat_atk_bonus = values["runtime_flat"]
        character.runtime_atk_flat_bonus = values["runtime_flat"]


def _merge_components(target: dict[str, Any], source: dict[str, Any]) -> None:
    normalized = normalize_stat_components(source)
    for stat, values in normalized.items():
        explicit_source = source.get(stat) if isinstance(source.get(stat), dict) else {}
        for field, value in values.items():
            if value is None:
                _set_component_value(target, stat, field, None)
            elif (field in explicit_source) or any(old in source for old, alias in LEGACY_ATTACK_ALIASES.items() if alias == (stat, field)):
                _set_component_value(target, stat, field, value)
    for old_name, (stat, field) in LEGACY_ATTACK_ALIASES.items():
        if old_name in source:
            _set_component_value(target, stat, field, source[old_name])


def _merge_runtime_bonuses(target: dict[str, Any], source: dict[str, Any]) -> None:
    for stat in COMPONENT_STATS:
        stat_source = source.get(stat) if isinstance(source.get(stat), dict) else {}
        if "percent" in stat_source:
            _set_component_value(target, stat, "runtime_percent", stat_source.get("percent"))
        if "flat" in stat_source:
            _set_component_value(target, stat, "runtime_flat", stat_source.get("flat"))


def _apply_override_to_components(components: dict[str, Any], field_name: str, value: Any) -> None:
    if field_name in LEGACY_ATTACK_ALIASES:
        stat, field = LEGACY_ATTACK_ALIASES[field_name]
        _set_component_value(components, stat, field, value)
        return
    dotted = field_name.split(".")
    if len(dotted) == 2 and dotted[0] in COMPONENT_STATS:
        field = dotted[1]
        if field in {"character_base", "weapon_base", "percent", "flat", "runtime_percent", "runtime_flat", "final_reference"}:
            _set_component_value(components, dotted[0], field, value)
            return
    flat_aliases = {
        "character_base_def": ("def", "character_base"),
        "static_def_percent": ("def", "percent"),
        "static_flat_def": ("def", "flat"),
        "runtime_def_percent_bonus": ("def", "runtime_percent"),
        "runtime_def_flat_bonus": ("def", "runtime_flat"),
        "final_def_reference": ("def", "final_reference"),
        "character_base_hp": ("hp", "character_base"),
        "static_hp_percent": ("hp", "percent"),
        "static_flat_hp": ("hp", "flat"),
        "runtime_hp_percent_bonus": ("hp", "runtime_percent"),
        "runtime_hp_flat_bonus": ("hp", "runtime_flat"),
        "final_hp_reference": ("hp", "final_reference"),
    }
    if field_name in flat_aliases:
        stat, field = flat_aliases[field_name]
        _set_component_value(components, stat, field, value)


def _set_component_value(components: dict[str, Any], stat: str, field: str, value: Any) -> None:
    components.setdefault(stat, {})
    components[stat][field] = value


def _required_component_fields_for_stat(stat: str) -> list[str]:
    if stat == "atk":
        return ["character_base", "weapon_base", "percent", "flat", "final_reference"]
    return ["character_base", "percent", "flat", "final_reference"]


def _required_damage_bonus_fields() -> list[str]:
    return [
        "damage_bonuses.all",
        "damage_bonuses.by_category.basic_attack",
        "damage_bonuses.by_category.heavy_attack",
        "damage_bonuses.by_category.resonance_skill",
        "damage_bonuses.by_category.resonance_liberation",
    ]


def _required_scaling_stats_from_summary(summary: dict[str, Any]) -> set[str]:
    required: set[str] = set()
    for stat in ("atk", "def", "hp"):
        if summary.get(f"actions_requiring_{stat}_stats"):
            required.add(stat)
    if not required:
        required.add("atk")
    return required


def _missing_required_stat_fields(summary: dict[str, Any], required_scaling_stats: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for stat in required_scaling_stats:
        for field in _required_component_fields_for_stat(stat):
            normalized_field = "final_reference" if field == "final_reference" else field
            value = (summary.get("stat_components") or {}).get(stat, {}).get(normalized_field)
            if value is None:
                missing.append(f"stat_components.{stat}.{field}")
    return missing


def _require_profile(character_id: str, profile_id: str, all_profiles: dict[str, Any]) -> None:
    if profile_id not in (all_profiles.get(character_id) or {}):
        available = sorted((all_profiles.get(character_id) or {}).keys())
        raise ValueError(
            f"Unknown build profile {profile_id!r} for {character_id!r}. "
            f"Available profiles: {available or 'none'}."
        )
