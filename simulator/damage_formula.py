from __future__ import annotations

from simulator.buff_system import buffed_stats
from simulator.models import ActionData, BuffData, CharacterData, CombatState


def expected_damage(
    character: CharacterData,
    action: ActionData,
    state: CombatState,
    buffs: dict[str, BuffData],
) -> float:
    if action.damage_multiplier <= 0.0:
        return 0.0

    attack, damage_bonus = buffed_stats(character, state, buffs)
    return (
        attack
        * action.damage_multiplier
        * (1.0 + damage_bonus)
        * (1.0 + character.crit_rate * character.crit_damage)
    )
