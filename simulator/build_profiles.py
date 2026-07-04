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
        normalized["by_category"][str(category)] = float(value)
    for element, value in (source.get("by_element") or {}).items():
        normalized["by_element"][str(element)] = float(value)

    fields = legacy_fields or {}
    if not damage_bonuses and legacy_all == 0.0 and fields.get("damage_bonus") is not None:
        normalized["all"] += float(fields.get("damage_bonus") or 0.0)
    if fields.get("elemental_dmg_bonus") is not None:
        normalized["by_element"]["generic"] = normalized["by_element"].get("generic", 0.0) + float(fields["elemental_dmg_bonus"])
    for field_name, category in LEGACY_CATEGORY_ALIASES.items():
        if fields.get(field_name) is not None:
            normalized["by_category"][category] = normalized["by_category"].get(category, 0.0) + float(fields[field_name])

    return normalized


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
) -> CharacterData:
    data = build_profiles if build_profiles is not None else load_build_profiles()
    profiles = (data.get("profiles") or {}).get(character_data.id, {})
    if profile_id is None:
        profile_id = "default" if "default" in profiles else None
    if profile_id is None:
        effective = character_data.model_copy(deep=True)
        effective.energy_regen = effective.energy_regen or 1.0
        effective.damage_bonuses = normalize_damage_bonuses({}, legacy_all=effective.dmg_bonus)
        return effective
    _require_profile(character_data.id, profile_id, data.get("profiles") or {})

    effective = character_data.model_copy(deep=True)
    effective.energy_regen = effective.energy_regen or 1.0
    effective.damage_bonuses = normalize_damage_bonuses(
        effective.damage_bonuses,
        legacy_all=effective.dmg_bonus,
        legacy_fields=effective.model_dump(mode="json"),
    )

    for resolved_id, profile in _profile_lineage(character_data.id, profile_id, profiles):
        for stat_name, stat_value in (profile.get("stat_overrides") or {}).items():
            _apply_stat_override(effective, stat_name, stat_value)
        effective.damage_bonuses = merge_damage_bonuses(effective.damage_bonuses, profile.get("damage_bonuses"))
        effective.build_profile_id = resolved_id
        effective.build_profile_display_name = profile.get("display_name", resolved_id)
        effective.build_profile_description = profile.get("description")

    return effective


def action_damage_bonus_category(action: ActionData) -> str:
    explicit = getattr(action, "damage_bonus_category", None)
    if explicit:
        return str(explicit)
    tags = set(action.tags or [])
    for tag in ("intro", "outro", "coordinated_attack"):
        if tag in tags:
            return tag
    if action.action_type in DAMAGE_BONUS_CATEGORIES:
        return action.action_type
    return "other"


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
        "damage_element": element,
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
            "energy_regen": character.energy_regen,
            "crit_rate": character.crit_rate,
            "crit_damage": character.crit_damage,
            "damage_bonuses": character.damage_bonuses,
        }
        for character_id, character in characters.items()
    }


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


def _require_profile(character_id: str, profile_id: str, all_profiles: dict[str, Any]) -> None:
    if profile_id not in (all_profiles.get(character_id) or {}):
        available = sorted((all_profiles.get(character_id) or {}).keys())
        raise ValueError(
            f"Unknown build profile {profile_id!r} for {character_id!r}. "
            f"Available profiles: {available or 'none'}."
        )
