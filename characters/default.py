from __future__ import annotations

from characters.base import CharacterMechanic


class DefaultCharacterMechanic(CharacterMechanic):
    def __init__(self, character_id: str = "default") -> None:
        self.character_id = character_id

    def advance_time(self, state, combat_elapsed: float, action_elapsed: float | None = None) -> None:
        pass
