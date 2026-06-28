from __future__ import annotations

from simulator.models import CharacterData, CombatState


def create_initial_state(characters: dict[str, CharacterData]) -> CombatState:
    active = next((char for char in characters.values() if char.active), None)
    if active is None:
        active = next(iter(characters.values()))

    return CombatState(
        active_character_id=active.id,
        resonance_energy={char.id: char.resonance_energy for char in characters.values()},
        concerto_energy={char.id: char.concerto_energy for char in characters.values()},
    )
