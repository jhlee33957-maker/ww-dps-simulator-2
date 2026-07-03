from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
    path = Path(data_dir) / "party_presets.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as file:
        items = json.load(file)
    return {str(item["party_id"]): item for item in items}


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
