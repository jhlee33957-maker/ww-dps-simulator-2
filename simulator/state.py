from __future__ import annotations

from simulator.models import CharacterData, CombatState


def create_initial_state(characters: dict[str, CharacterData]) -> CombatState:
    active = next((char for char in characters.values() if char.active), None)
    if active is None:
        active = next(iter(characters.values()))

    return CombatState(
        active_character_id=active.id,
        resonance_energy={
            char.id: min(char.resonance_energy, char.resonance_energy_max)
            for char in characters.values()
        },
        concerto_energy={char.id: min(char.concerto_energy, 100.0) for char in characters.values()},
        wasted_resonance_energy={char.id: 0.0 for char in characters.values()},
        wasted_concerto_energy={char.id: 0.0 for char in characters.values()},
    )
