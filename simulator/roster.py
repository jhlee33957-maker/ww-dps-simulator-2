from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


ACCOUNT_PARTY_PRESET_OVERLAY = "account_party_presets_v122.json"


def parse_character_ids(value: str | list[str] | None, available_character_ids: list[str]) -> list[str]:
    if isinstance(value, str):
        requested = [item.strip() for item in value.split(",") if item.strip()]
    elif value is None:
        requested = []
    else:
        requested = [str(item).strip() for item in value if str(item).strip()]

    if not requested:
        if "aemeath" in available_character_ids:
            return ["aemeath"]
        return list(available_character_ids)

    available = set(available_character_ids)
    selected: list[str] = []
    for character_id in requested:
        if character_id not in available:
            raise ValueError(f"Unknown character_id {character_id!r}. Available: {', '.join(available_character_ids)}")
        if character_id not in selected:
            selected.append(character_id)
    return selected


def read_party_presets(data_dir: Path | str) -> dict[str, dict[str, Any]]:
    directory = Path(data_dir)
    base_path = directory / "party_presets.json"
    base_items = _read_party_items(base_path) if base_path.exists() else []
    merged: dict[str, dict[str, Any]] = {}
    for item in base_items:
        party_id = _party_id(item, base_path)
        if party_id in merged:
            raise ValueError(f"Duplicate base party ID: {party_id}")
        merged[party_id] = copy.deepcopy(item)

    overlay_path = directory / ACCOUNT_PARTY_PRESET_OVERLAY
    if not overlay_path.exists():
        return merged
    overlay = _read_json(overlay_path)
    items = overlay.get("parties") if isinstance(overlay, dict) else None
    if not isinstance(items, list):
        raise ValueError(f"Account party overlay must contain a parties list: {overlay_path}")
    seen_overlay_ids: set[str] = set()
    for item in items:
        party_id = _party_id(item, overlay_path)
        if party_id in seen_overlay_ids:
            raise ValueError(f"Duplicate account party overlay ID: {party_id}")
        seen_overlay_ids.add(party_id)
        if party_id in merged:
            raise ValueError(f"Account party overlay may add only new party IDs: {party_id}")
    known_character_ids = _known_character_ids(directory)
    for item in items:
        party_id = _party_id(item, overlay_path)
        _validate_account_party_overlay(item, directory, known_character_ids)
        merged[party_id] = copy.deepcopy(item)
    return merged


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _read_party_items(path: Path) -> list[dict[str, Any]]:
    items = _read_json(path)
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError(f"Party preset file must contain a list of objects: {path}")
    return items


def _party_id(item: Any, source: Path) -> str:
    if not isinstance(item, dict) or not str(item.get("party_id", "")).strip():
        raise ValueError(f"Party preset is missing party_id: {source}")
    return str(item["party_id"])


def _known_character_ids(data_dir: Path) -> set[str]:
    path = data_dir / "characters.json"
    items = _read_json(path)
    return {str(item["id"]) for item in items if isinstance(item, dict) and item.get("id")}


def _validate_account_party_overlay(item: dict[str, Any], data_dir: Path, known_character_ids: set[str]) -> None:
    party_id = _party_id(item, data_dir / ACCOUNT_PARTY_PRESET_OVERLAY)
    members = item.get("members")
    if not isinstance(members, list) or not members or len(members) != len(set(members)):
        raise ValueError(f"Account party {party_id} must have unique members")
    unknown_members = sorted(set(map(str, members)) - known_character_ids)
    if unknown_members:
        raise ValueError(f"Account party {party_id} references unknown characters: {unknown_members}")
    if item.get("initial_active") not in members:
        raise ValueError(f"Account party {party_id} has invalid initial_active")
    profiles = item.get("build_profiles")
    if not isinstance(profiles, dict) or set(profiles) != set(members):
        raise ValueError(f"Account party {party_id} must declare one build profile per member")

    from simulator.account_constellation_effects import validate_account_single_boss_scope
    from simulator.account_profile_gate import validate_profile_simulation_readiness
    from simulator.build_profiles import load_build_profiles

    scope = item.get("account_scope")
    if not isinstance(scope, dict):
        raise ValueError(f"Account party {party_id} must include an explicit account_scope")
    validate_account_single_boss_scope(scope)
    all_profiles = (load_build_profiles(data_dir).get("profiles") or {})
    for character_id, profile_id in profiles.items():
        profile = (all_profiles.get(character_id) or {}).get(profile_id)
        if not isinstance(profile, dict):
            raise ValueError(f"Account party {party_id} references unknown build profile {character_id}:{profile_id}")
        if not profile.get("account_profile") or not profile.get("simulation_ready"):
            raise ValueError(f"Account party {party_id} requires simulation-ready account profile {character_id}:{profile_id}")
        validate_profile_simulation_readiness(profile, account_scope=scope, precombat_elapsed_seconds=0.0)

    aemeath = ((item.get("mechanic_overrides") or {}).get("aemeath") or {})
    mode = aemeath.get("aemeath_resonance_mode")
    if mode not in {"tune_rupture", "fusion_burst"}:
        raise ValueError(f"Account party {party_id} must specify a resolved Aemeath resonance mode")


def resolve_party_preset(
    value: str | list[str] | None,
    party_presets: dict[str, dict[str, Any]] | None = None,
) -> tuple[str | list[str] | None, str | None]:
    if isinstance(value, str) and party_presets and value in party_presets:
        preset = party_presets[value]
        return list(preset["members"]), preset.get("initial_active")
    return value, None


def parse_party_character_ids(
    value: str | list[str] | None,
    available_characters: dict[str, Any],
    party_presets: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    available_character_ids = list(available_characters)
    value, _initial_active = resolve_party_preset(value, party_presets)
    requested = parse_character_ids(value, available_character_ids) if value else []
    if not requested:
        if "aemeath" in available_characters:
            requested = ["aemeath"]
        else:
            requested = [
                character_id
                for character_id, character in available_characters.items()
                if not is_dummy_character(character)
            ] or available_character_ids
    if not 1 <= len(requested) <= 3:
        raise ValueError("A party must contain 1 to 3 characters.")
    return requested


def get_initial_active_character(selected_character_ids: list[str], requested: str | None = None) -> str:
    if not selected_character_ids:
        raise ValueError("At least one selected character is required.")
    if requested is not None:
        if requested not in selected_character_ids:
            raise ValueError(f"Initial active character {requested!r} is not in the selected roster.")
        return requested
    return selected_character_ids[0]


def is_dummy_character(character: Any) -> bool:
    data_status = getattr(character, "data_status", None)
    is_dummy_sample = getattr(character, "is_dummy_sample", False)
    if isinstance(character, dict):
        data_status = character.get("data_status", data_status)
        is_dummy_sample = character.get("is_dummy_sample", is_dummy_sample)
    return data_status == "dummy_sample" or bool(is_dummy_sample)


def is_swap_action(action: Any) -> bool:
    return getattr(action, "action_type", None) == "swap" or (
        isinstance(action, dict) and action.get("action_type") == "swap"
    )


def get_swap_target_character_id(action: Any) -> str | None:
    if isinstance(action, dict):
        return action.get("character_id")
    return getattr(action, "character_id", None)
