from __future__ import annotations

from characters.aemeath import AemeathMechanic
from characters.base import CharacterMechanic
from characters.default import DefaultCharacterMechanic


def get_mechanic(character_id: str) -> CharacterMechanic:
    if character_id == "aemeath":
        return AemeathMechanic()
    return DefaultCharacterMechanic(character_id)


def get_mechanics_for_characters(character_ids: list[str]) -> dict[str, CharacterMechanic]:
    return {character_id: get_mechanic(character_id) for character_id in character_ids}
