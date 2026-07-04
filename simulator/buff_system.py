from __future__ import annotations

from typing import Any

from simulator.models import ActiveBuff, BuffData, CharacterData, CombatState


def tick_buffs(state: CombatState, elapsed: float) -> None:
    remaining: list[ActiveBuff] = []
    for buff in state.active_buffs:
        buff.remaining_duration = max(0.0, buff.remaining_duration - elapsed)
        if buff.remaining_duration > 0.0:
            remaining.append(buff)
    state.active_buffs = remaining
    state.team_buffs = list(remaining)


def apply_buff(state: CombatState, buff: BuffData, source_character_id: str | None) -> None:
    state.active_buffs = [active for active in state.active_buffs if active.buff_id != buff.id]
    state.active_buffs.append(
        ActiveBuff(
            buff_id=buff.id,
            source_character_id=source_character_id,
            remaining_duration=buff.duration,
            stack_count=min(buff.stack_count, buff.max_stacks),
            target_character_id=buff.target_character_id,
            metadata=buff.metadata,
        )
    )
    state.team_buffs = list(state.active_buffs)


def add_team_buff(party_state: CombatState, buff: BuffData, source_character_id: str | None = None) -> None:
    apply_buff(party_state, buff, source_character_id)


def tick_team_buffs(party_state: CombatState, action_time: float) -> None:
    tick_buffs(party_state, action_time)


def has_required_buffs(state: CombatState, required_buffs: list[str]) -> bool:
    active_ids = {buff.buff_id for buff in state.active_buffs}
    return all(buff_id in active_ids for buff_id in required_buffs)


def _buff_applies(buff: BuffData, active: ActiveBuff, character: CharacterData, state: CombatState) -> bool:
    target_scope = buff.target_scope or buff.target
    return (
        target_scope in {"team", "party"}
        or target_scope == "enemy"
        or (target_scope == "active" and character.id == state.active_character_id)
        or (target_scope == "next_active" and character.id == state.active_character_id and active.source_character_id != character.id)
        or (target_scope == "self" and active.source_character_id == character.id)
        or (target_scope == "specific_character" and (buff.target_character_id or active.target_character_id) == character.id)
    )


def _tags_match(buff: BuffData, action: Any | None) -> bool:
    if not buff.affected_tags:
        return True
    action_tags = set(getattr(action, "tags", []) or [])
    return bool(action_tags.intersection(buff.affected_tags))


def get_active_buffs_for_action(
    actor_character_id: str,
    action: Any,
    state: CombatState,
    buffs: dict[str, BuffData],
    *,
    time_offset: float = 0.0,
) -> list[tuple[ActiveBuff, BuffData]]:
    character = CharacterData(
        id=actor_character_id,
        name=actor_character_id,
        resonance_energy=0.0,
        concerto_energy=0.0,
    )
    active_pairs: list[tuple[ActiveBuff, BuffData]] = []
    for active in state.active_buffs:
        if active.remaining_duration <= time_offset:
            continue
        buff = buffs[active.buff_id]
        if not _buff_applies(buff, active, character, state):
            continue
        if not _tags_match(buff, action):
            continue
        active_pairs.append((active, buff))
    return active_pairs


def damage_amp_for_action(
    actor_character_id: str,
    action: Any,
    state: CombatState,
    buffs: dict[str, BuffData],
    *,
    time_offset: float = 0.0,
) -> float:
    damage_amp = 0.0
    for active, buff in get_active_buffs_for_action(
        actor_character_id,
        action,
        state,
        buffs,
        time_offset=time_offset,
    ):
        buff_value = float(active.metadata.get("dynamic_value", buff.value))
        damage_amp += buff.damage_amp_modifiers.get("all", 0.0)
        for tag in getattr(action, "tags", []) or []:
            damage_amp += buff.damage_amp_modifiers.get(tag, 0.0)
        if buff.modifier_type == "damage_amp":
            damage_amp += buff_value
    return damage_amp


def apply_buff_modifiers_to_damage_context(damage: float, damage_amp: float) -> float:
    return damage * (1.0 + damage_amp)


def buffed_combat_stats(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
    time_offset: float = 0.0,
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
    active_buff_names: list[str] = []

    for active in state.active_buffs:
        if active.remaining_duration <= time_offset:
            continue
        buff = buffs[active.buff_id]
        if not _buff_applies(buff, active, character, state):
            continue
        buff_value = float(active.metadata.get("dynamic_value", buff.value))
        active_buff_names.append(buff.id)
        if buff.modifier_type == "attack":
            stats["atk_percent"] += buff_value
        elif buff.modifier_type == "damage_bonus":
            stats["dmg_bonus"] += buff_value
        elif buff.modifier_type == "boost":
            stats["boost"] += buff_value
        elif buff.modifier_type == "dmg_taken":
            stats["dmg_taken"] += buff_value
        for stat_name, stat_value in buff.stat_modifiers.items():
            if stat_name in stats:
                stats[stat_name] += stat_value

    stats["active_buff_count"] = float(len(active_buff_names))
    stats["active_buff_summary"] = active_buff_names
    return stats


def buffed_stats(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
) -> tuple[float, float]:
    stats = buffed_combat_stats(character, state, buffs)
    attack = (stats["character_base_atk"] + stats["weapon_base_atk"]) * (1.0 + stats["atk_percent"]) + stats["flat_atk"]
    return attack, stats["dmg_bonus"]
