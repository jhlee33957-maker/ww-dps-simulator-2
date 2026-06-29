from __future__ import annotations

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
