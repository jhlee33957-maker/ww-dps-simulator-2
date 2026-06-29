from __future__ import annotations

from simulator.models import CharacterData, CombatState, EnemyData


def create_initial_state(
    characters: dict[str, CharacterData],
    enemy: EnemyData | None = None,
    active_character_id: str | None = None,
) -> CombatState:
    if active_character_id is not None:
        active = characters[active_character_id]
    else:
        active = next((char for char in characters.values() if char.active), None)
        if active is None:
            active = next(iter(characters.values()))
    enemy = enemy or EnemyData()

    return CombatState(
        active_character_id=active.id,
        enemy_level=enemy.level,
        enemy_res=enemy.res,
        res_pen=enemy.res_pen,
        def_reduction=enemy.def_reduction,
        dmg_taken=enemy.dmg_taken,
        tune_dmg_bonus=enemy.tune_dmg_bonus,
        resonance_energy={
            char.id: min(char.resonance_energy, char.resonance_energy_max)
            for char in characters.values()
        },
        concerto_energy={char.id: min(char.concerto_energy, 100.0) for char in characters.values()},
        wasted_resonance_energy={char.id: 0.0 for char in characters.values()},
        wasted_concerto_energy={char.id: 0.0 for char in characters.values()},
    )
