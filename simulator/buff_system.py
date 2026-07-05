from __future__ import annotations

from typing import Any

from simulator.models import ActiveBuff, BuffData, CharacterData, CombatState


def _recalculate_attack_stats(stats: dict[str, Any]) -> None:
    base_attack_total = float(stats.get("character_base_atk", 0.0)) + float(stats.get("weapon_base_atk", 0.0))
    static_attack = (
        base_attack_total * (1.0 + float(stats.get("static_atk_percent", 0.0)))
        + float(stats.get("static_flat_atk", 0.0))
    )
    effective_attack = (
        static_attack
        + base_attack_total * float(stats.get("runtime_atk_percent_bonus", 0.0))
        + float(stats.get("runtime_flat_atk_bonus", 0.0))
    )
    stats["base_attack_total"] = base_attack_total
    stats["static_attack"] = static_attack
    stats["effective_attack"] = effective_attack
    stats["atk_percent"] = float(stats.get("static_atk_percent", 0.0)) + float(stats.get("runtime_atk_percent_bonus", 0.0))
    stats["flat_atk"] = float(stats.get("static_flat_atk", 0.0)) + float(stats.get("runtime_flat_atk_bonus", 0.0))
    reference = stats.get("final_attack_reference")
    stats["attack_reference_delta"] = None
    stats["attack_reference_delta_percent"] = None
    if reference not in (None, 0):
        stats["attack_reference_delta"] = static_attack - float(reference)
        stats["attack_reference_delta_percent"] = stats["attack_reference_delta"] / float(reference)


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


def collect_runtime_atk_percent_bonus(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
    time_offset: float = 0.0,
) -> float:
    return float(buffed_combat_stats(character, state, buffs, time_offset=time_offset)["runtime_atk_percent_bonus"])


def collect_runtime_flat_atk_bonus(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
    time_offset: float = 0.0,
) -> float:
    return float(buffed_combat_stats(character, state, buffs, time_offset=time_offset)["runtime_flat_atk_bonus"])


def buffed_combat_stats(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
    time_offset: float = 0.0,
) -> dict[str, float]:
    stats = {
        "character_base_atk": character.character_base_atk,
        "weapon_base_atk": character.weapon_base_atk,
        "base_attack_total": character.base_attack_total,
        "static_atk_percent": character.static_atk_percent,
        "static_flat_atk": character.static_flat_atk,
        "runtime_atk_percent_bonus": character.runtime_atk_percent_bonus,
        "runtime_flat_atk_bonus": character.runtime_flat_atk_bonus,
        "static_attack": character.static_attack,
        "effective_attack": character.effective_attack,
        "final_attack_reference": character.final_attack_reference,
        "attack_reference_delta": character.attack_reference_delta,
        "attack_reference_delta_percent": character.attack_reference_delta_percent,
        "atk_percent": character.static_atk_percent + character.runtime_atk_percent_bonus,
        "flat_atk": character.static_flat_atk + character.runtime_flat_atk_bonus,
        "dmg_bonus": character.dmg_bonus,
        "crit_rate": character.crit_rate,
        "crit_damage": character.crit_damage,
        "boost": character.boost,
        "attacker_level": float(character.attacker_level),
        "def_ignore": character.def_ignore,
        "final_dmg_bonus": character.final_dmg_bonus,
        "dmg_taken": state.dmg_taken,
        "damage_bonus_buff": 0.0,
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
            stats["runtime_atk_percent_bonus"] += buff_value
        elif buff.modifier_type == "damage_bonus":
            stats["dmg_bonus"] += buff_value
            stats["damage_bonus_buff"] += buff_value
        elif buff.modifier_type == "boost":
            stats["boost"] += buff_value
        elif buff.modifier_type == "dmg_taken":
            stats["dmg_taken"] += buff_value
        for stat_name, stat_value in buff.stat_modifiers.items():
            if stat_name == "atk_percent":
                stats["runtime_atk_percent_bonus"] += stat_value
            elif stat_name == "flat_atk":
                stats["runtime_flat_atk_bonus"] += stat_value
            elif stat_name in stats:
                stats[stat_name] += stat_value

    _recalculate_attack_stats(stats)
    stats["active_buff_count"] = float(len(active_buff_names))
    stats["active_buff_summary"] = active_buff_names
    return stats


def buffed_stats(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
) -> tuple[float, float]:
    stats = buffed_combat_stats(character, state, buffs)
    return stats["effective_attack"], stats["dmg_bonus"]
