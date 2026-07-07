from __future__ import annotations

from characters.aemeath import AemeathMechanic
from characters.base import CharacterMechanic
from characters.default import DefaultCharacterMechanic
from characters.lynae import LynaeMechanic
from characters.mornye import MornyeMechanic


def get_mechanic(character_id: str) -> CharacterMechanic:
    if character_id == "aemeath":
        return AemeathMechanic()
    if character_id == "mornye":
        return MornyeMechanic()
    if character_id == "lynae":
        return LynaeMechanic()
    return DefaultCharacterMechanic(character_id)


def get_mechanics_for_characters(character_ids: list[str]) -> dict[str, CharacterMechanic]:
    return {character_id: get_mechanic(character_id) for character_id in character_ids}


def resolve_incoming_qte_transition_action(
    character_id: str,
    character_state: dict,
    transition_config: dict,
) -> tuple[str | None, list[str]]:
    mechanic = get_mechanic(character_id)
    return mechanic.resolve_incoming_qte_transition_action(character_state, transition_config)
