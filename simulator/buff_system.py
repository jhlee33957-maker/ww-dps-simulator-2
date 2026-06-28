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


def _buff_applies(buff: BuffData, active: ActiveBuff, character: CharacterData, state: CombatState) -> bool:
    return (
        buff.target == "team"
        or (buff.target == "active" and character.id == state.active_character_id)
        or (buff.target == "self" and active.source_character_id == character.id)
    )


def buffed_combat_stats(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
) -> dict[str, float]:
    stats = {
        "character_base_atk": character.character_base_atk,
        "weapon_base_atk": character.weapon_base_atk,
        "atk_percent": character.atk_percent,
        "flat_atk": character.flat_atk,
        "dmg_bonus": character.dmg_bonus,
        "crit_rate": character.crit_rate,
        "crit_damage": character.crit_damage,
        "boost": character.boost,
        "attacker_level": float(character.attacker_level),
        "def_ignore": character.def_ignore,
        "final_dmg_bonus": character.final_dmg_bonus,
        "dmg_taken": state.dmg_taken,
    }

    for active in state.active_buffs:
        buff = buffs[active.buff_id]
        if not _buff_applies(buff, active, character, state):
            continue
        if buff.modifier_type == "attack":
            stats["atk_percent"] += buff.value
        elif buff.modifier_type == "damage_bonus":
            stats["dmg_bonus"] += buff.value
        elif buff.modifier_type == "boost":
            stats["boost"] += buff.value
        elif buff.modifier_type == "dmg_taken":
            stats["dmg_taken"] += buff.value

    return stats


def buffed_stats(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
) -> tuple[float, float]:
    stats = buffed_combat_stats(character, state, buffs)
    attack = (stats["character_base_atk"] + stats["weapon_base_atk"]) * (1.0 + stats["atk_percent"]) + stats["flat_atk"]
    return attack, stats["dmg_bonus"]
