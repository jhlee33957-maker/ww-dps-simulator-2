from __future__ import annotations

from simulator.models import ActiveBuff, BuffData, CharacterData, CombatState


def tick_buffs(state: CombatState, elapsed: float) -> None:
    remaining: list[ActiveBuff] = []
    for buff in state.active_buffs:
        buff.remaining_duration = max(0.0, buff.remaining_duration - elapsed)
        if buff.remaining_duration > 0.0:
            remaining.append(buff)
    state.active_buffs = remaining


def apply_buff(state: CombatState, buff: BuffData, source_character_id: str | None) -> None:
    state.active_buffs = [active for active in state.active_buffs if active.buff_id != buff.id]
    state.active_buffs.append(
        ActiveBuff(
            buff_id=buff.id,
            source_character_id=source_character_id,
            remaining_duration=buff.duration,
        )
    )


def has_required_buffs(state: CombatState, required_buffs: list[str]) -> bool:
    active_ids = {buff.buff_id for buff in state.active_buffs}
    return all(buff_id in active_ids for buff_id in required_buffs)


def buffed_stats(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
) -> tuple[float, float]:
    attack = character.attack
    damage_bonus = character.damage_bonus

    for active in state.active_buffs:
        buff = buffs[active.buff_id]
        applies = (
            buff.target == "team"
            or (buff.target == "active" and character.id == state.active_character_id)
            or (buff.target == "self" and active.source_character_id == character.id)
        )
        if not applies:
            continue

        if buff.modifier_type == "attack":
            attack *= 1.0 + buff.value
        elif buff.modifier_type == "damage_bonus":
            damage_bonus += buff.value

    return attack, damage_bonus
