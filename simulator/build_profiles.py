from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
ATTACK_COMPONENT_FIELDS = {
    "character_base_atk",
    "weapon_base_atk",
    "static_atk_percent",
    "static_flat_atk",
    "runtime_atk_percent_bonus",
    "runtime_flat_atk_bonus",
    "final_attack_reference",
}
COMBAT_STAT_FIELDS = {"crit_rate", "crit_damage", "energy_regen"}
REAL_REQUIRED_FIELDS = [
    "stat_components.character_base_atk",
    "stat_components.weapon_base_atk",
    "stat_components.static_atk_percent",
    "stat_components.static_flat_atk",
    "stat_components.final_attack_reference",
    "combat_stats.crit_rate",
    "combat_stats.crit_damage",
    "combat_stats.energy_regen",
    "damage_bonuses.all",
    "damage_bonuses.by_category.basic_attack",
    "damage_bonuses.by_category.heavy_attack",
    "damage_bonuses.by_category.resonance_skill",
    "damage_bonuses.by_category.resonance_liberation",
]
DEFAULT_ATTACK_REFERENCE_TOLERANCE = 0.01


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
    base_attack_total = float(character_base_atk) + float(weapon_base_atk)
    static_attack = base_attack_total * (1.0 + float(static_atk_percent)) + float(static_flat_atk)
    effective_attack = (
        static_attack
        + base_attack_total * float(runtime_atk_percent_bonus)
        + float(runtime_flat_atk_bonus)
    )
    attack_reference_delta = None
    attack_reference_delta_percent = None
    if final_attack_reference not in (None, 0):
        reference = float(final_attack_reference)
        attack_reference_delta = static_attack - reference
        attack_reference_delta_percent = attack_reference_delta / reference
    return {
        "character_base_atk": float(character_base_atk),
        "weapon_base_atk": float(weapon_base_atk),
        "base_attack_total": base_attack_total,
        "static_atk_percent": float(static_atk_percent),
        "static_flat_atk": float(static_flat_atk),
        "runtime_atk_percent_bonus": float(runtime_atk_percent_bonus),
        "runtime_flat_atk_bonus": float(runtime_flat_atk_bonus),
        "static_attack": static_attack,
        "effective_attack": effective_attack,
        "final_attack_reference": None if final_attack_reference is None else float(final_attack_reference),
        "attack_reference_delta": attack_reference_delta,
        "attack_reference_delta_percent": attack_reference_delta_percent,
    }


def apply_attack_components_to_character(
    character: CharacterData,
    components: dict[str, Any],
    *,
    tolerance: float = DEFAULT_ATTACK_REFERENCE_TOLERANCE,
) -> CharacterData:
    calculated = calculate_attack_components(
        character_base_atk=float(components.get("character_base_atk") or 0.0),
        weapon_base_atk=float(components.get("weapon_base_atk") or 0.0),
        static_atk_percent=float(components.get("static_atk_percent") or 0.0),
        static_flat_atk=float(components.get("static_flat_atk") or 0.0),
        runtime_atk_percent_bonus=float(components.get("runtime_atk_percent_bonus") or 0.0),
        runtime_flat_atk_bonus=float(components.get("runtime_flat_atk_bonus") or 0.0),
        final_attack_reference=components.get("final_attack_reference"),
    )
    for field_name, value in calculated.items():
        setattr(character, field_name, value)
    character.atk_percent = character.static_atk_percent
    character.flat_atk = character.static_flat_atk
    character.attack = character.effective_attack
    if (
        character.attack_reference_delta_percent is not None
        and abs(character.attack_reference_delta_percent) > tolerance
    ):
        warning = (
            "Calculated ATK does not match final_attack_reference. "
            "Check base ATK, weapon ATK, ATK%, and flat ATK inputs."
        )
        if warning not in character.profile_warnings:
            character.profile_warnings.append(warning)
    return character


def character_stat_components_from_legacy(character: CharacterData) -> dict[str, Any]:
    return {
        "character_base_atk": character.character_base_atk,
        "weapon_base_atk": character.weapon_base_atk,
        "static_atk_percent": character.static_atk_percent if character.static_atk_percent else character.atk_percent,
        "static_flat_atk": character.static_flat_atk if character.static_flat_atk else character.flat_atk,
        "runtime_atk_percent_bonus": character.runtime_atk_percent_bonus,
        "runtime_flat_atk_bonus": character.runtime_flat_atk_bonus,
        "final_attack_reference": character.final_attack_reference,
    }


def parse_stat_overrides(values: list[str] | tuple[str, ...] | None) -> dict[str, dict[str, float]]:
    overrides: dict[str, dict[str, float]] = {}
    allowed = ATTACK_COMPONENT_FIELDS | COMBAT_STAT_FIELDS
    for raw_value in values or []:
        parts = [part.strip() for part in raw_value.split(":")]
        if len(parts) != 3 or not all(parts):
            raise ValueError(f"Stat override must use character_id:field:value, got {raw_value!r}.")
        character_id, field_name, value_text = parts
        if field_name not in allowed:
            raise ValueError(f"Unknown stat override field {field_name!r}. Allowed fields: {sorted(allowed)}.")
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
        effective.damage_bonuses = normalize_damage_bonuses({}, legacy_all=effective.dmg_bonus)
        effective.profile_completeness_status = "fallback_character_stats"
        effective.implementation_status = effective.implementation_status or "character_data_fallback"
        apply_attack_components_to_character(effective, character_stat_components_from_legacy(effective))
        return effective
    _require_profile(character_data.id, profile_id, data.get("profiles") or {})

    effective = character_data.model_copy(deep=True)
    effective.energy_regen = effective.energy_regen or 1.0
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
        for stat_name, stat_value in (profile.get("stat_components") or {}).items():
            if stat_name in ATTACK_COMPONENT_FIELDS and stat_value is not None:
                components[stat_name] = stat_value
        for stat_name, stat_value in (profile.get("stat_overrides") or {}).items():
            _apply_stat_override(effective, stat_name, stat_value)
            if stat_name == "atk_percent":
                components["static_atk_percent"] = stat_value
            elif stat_name == "flat_atk":
                components["static_flat_atk"] = stat_value
            elif stat_name in ATTACK_COMPONENT_FIELDS:
                components[stat_name] = stat_value
        for stat_name, stat_value in (profile.get("combat_stats") or {}).items():
            if stat_name in COMBAT_STAT_FIELDS and stat_value is not None:
                setattr(effective, stat_name, float(stat_value))
        effective.damage_bonuses = merge_damage_bonuses(effective.damage_bonuses, profile.get("damage_bonuses"))
        if profile.get("damage_bonus") is not None and not (profile.get("damage_bonuses") or {}).get("all"):
            effective.damage_bonuses = merge_damage_bonuses(effective.damage_bonuses, {"all": profile.get("damage_bonus")})
        effective.build_profile_id = resolved_id
        effective.build_profile_display_name = profile.get("display_name", resolved_id)
        effective.build_profile_description = profile.get("description")
        effective.implementation_status = profile.get("implementation_status", effective.implementation_status)

    for stat_name, stat_value in (stat_overrides or {}).items():
        if stat_name in ATTACK_COMPONENT_FIELDS:
            components[stat_name] = stat_value
        elif stat_name in COMBAT_STAT_FIELDS:
            setattr(effective, stat_name, float(stat_value))
        else:
            raise ValueError(f"Unknown stat override {stat_name!r} for {character_data.id}.")

    effective.energy_regen = effective.energy_regen or 1.0
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
    apply_attack_components_to_character(
        effective,
        components,
        tolerance=float((data.get("attack_reference_tolerance") or DEFAULT_ATTACK_REFERENCE_TOLERANCE)),
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
        return str(explicit)
    for tag in action.tags or []:
        if tag in ELEMENT_KEYS:
            return tag
    for attr_name in ("damage_attribute", "element"):
        if character is not None:
            value = getattr(character, attr_name, None)
            if value:
                return str(value)
    return "generic"


def damage_bonus_breakdown(
    character: CharacterData,
    action: ActionData,
    *,
    additive_buff_bonus: float = 0.0,
) -> dict[str, Any]:
    bonuses = normalize_damage_bonuses(character.damage_bonuses, legacy_all=0.0 if character.damage_bonuses else character.dmg_bonus)
    category = action_damage_bonus_category(action)
    element = action_damage_element(action, character)
    all_bonus = float(bonuses.get("all", 0.0)) + float(additive_buff_bonus)
    category_bonus = float((bonuses.get("by_category") or {}).get(category, 0.0))
    element_bonuses = bonuses.get("by_element") or {}
    element_bonus = float(element_bonuses.get(element, element_bonuses.get("generic", 0.0) if element == "generic" else 0.0))
    return {
        "damage_category": category,
        "damage_bonus_category": category,
        "damage_element": element,
        "raw_skill_category": getattr(action, "raw_skill_category", None),
        "raw_damage_type": getattr(action, "raw_damage_type", None),
        "all_dmg_bonus": all_bonus,
        "category_dmg_bonus": category_bonus,
        "element_dmg_bonus": element_bonus,
        "effective_damage_bonus": all_bonus + category_bonus + element_bonus,
        "build_profile_id": character.build_profile_id,
    }


def effective_build_stats_summary(characters: dict[str, CharacterData]) -> dict[str, Any]:
    return {
        character_id: {
            "build_profile_id": character.build_profile_id,
            "display_name": character.build_profile_display_name,
            "implementation_status": character.implementation_status,
            "profile_completeness_status": character.profile_completeness_status,
            "missing_required_fields": character.missing_required_fields,
            "profile_warnings": character.profile_warnings,
            "character_base_atk": character.character_base_atk,
            "weapon_base_atk": character.weapon_base_atk,
            "base_attack_total": character.base_attack_total,
            "static_atk_percent": character.static_atk_percent,
            "static_flat_atk": character.static_flat_atk,
            "runtime_atk_percent_bonus": character.runtime_atk_percent_bonus,
            "runtime_flat_atk_bonus": character.runtime_flat_atk_bonus,
            "static_attack": character.static_attack,
            "effective_attack": character.effective_attack,
            "final_attack_reference": character.final_attack_reference,
            "attack_reference_delta": character.attack_reference_delta,
            "attack_reference_delta_percent": character.attack_reference_delta_percent,
            "energy_regen": character.energy_regen,
            "crit_rate": character.crit_rate,
            "crit_damage": character.crit_damage,
            "damage_bonuses": character.damage_bonuses,
        }
        for character_id, character in characters.items()
    }


def profile_missing_required_fields(profile: dict[str, Any], damage_bonuses: dict[str, Any] | None = None) -> list[str]:
    missing: list[str] = []
    stat_components = profile.get("stat_components") or {}
    combat_stats = profile.get("combat_stats") or {}
    profile_damage_bonuses = profile.get("damage_bonuses") or {}
    normalized_damage_bonuses = normalize_damage_bonuses(profile_damage_bonuses or damage_bonuses)
    for field_path in REAL_REQUIRED_FIELDS:
        group, field_name, *rest = field_path.split(".")
        value: Any = None
        if group == "stat_components":
            value = stat_components.get(field_name)
        elif group == "combat_stats":
            value = combat_stats.get(field_name)
        elif group == "damage_bonuses":
            if field_name == "all":
                value = (profile_damage_bonuses or {}).get("all")
            elif field_name == "by_category" and rest:
                value = ((profile_damage_bonuses or {}).get("by_category") or {}).get(rest[0])
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
        missing = summary.get("missing_required_fields") or []
        if implementation_status == "user_supplied_required" and missing:
            errors.append(
                f"{character_id}:{summary.get('build_profile_id')} is incomplete; missing fields: {', '.join(missing)}"
            )
        if implementation_status == "test_assumption" or implementation_status == "configurable_test_assumption":
            if allow_test_assumptions:
                warnings.append(
                    f"{character_id}:{summary.get('build_profile_id')} uses test-assumption stat profiles, not verified real-game stats."
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
    alias_map = {
        "atk_percent": "static_atk_percent",
        "flat_atk": "static_flat_atk",
    }
    stat_components = profile.get("stat_components") or {}
    for old_name, new_name in alias_map.items():
        if old_name in profile and new_name not in stat_components:
            components[new_name] = profile[old_name]
        elif old_name in profile and new_name in stat_components and profile[old_name] != stat_components[new_name]:
            warnings.append(f"Build profile has conflicting {old_name} and {new_name}; using {new_name}.")
    if "damage_bonus" in profile and not (profile.get("damage_bonuses") or {}).get("all"):
        warnings.append("Build profile uses legacy damage_bonus; normalized as damage_bonuses.all.")
    elif "damage_bonus" in profile and (profile.get("damage_bonuses") or {}).get("all") != profile["damage_bonus"]:
        warnings.append("Build profile has conflicting damage_bonus and damage_bonuses.all; using damage_bonuses.all.")


def _require_profile(character_id: str, profile_id: str, all_profiles: dict[str, Any]) -> None:
    if profile_id not in (all_profiles.get(character_id) or {}):
        available = sorted((all_profiles.get(character_id) or {}).keys())
        raise ValueError(
            f"Unknown build profile {profile_id!r} for {character_id!r}. "
            f"Available profiles: {available or 'none'}."
        )
