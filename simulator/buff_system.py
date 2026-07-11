from __future__ import annotations

from typing import Any

from simulator.build_profiles import normalize_support_stats, stat_component_log_fields, support_stat_log_fields
from simulator.models import ActiveBuff, BuffData, CharacterData, CombatState


def _recalculate_scaling_stats(stats: dict[str, Any]) -> None:
    for stat in ("atk", "def", "hp"):
        character_base = float(stats.get(f"character_base_{stat}", 0.0))
        weapon_base = float(stats.get(f"weapon_base_{stat}", 0.0))
        base_total = character_base + weapon_base
        static_value = (
            base_total * (1.0 + float(stats.get(f"static_{stat}_percent", 0.0)))
            + float(stats.get(f"static_flat_{stat}", 0.0))
        )
        runtime_flat = float(stats.get(f"runtime_{stat}_flat_bonus", 0.0))
        if stat == "atk":
            runtime_flat = float(stats.get("runtime_flat_atk_bonus", runtime_flat))
        effective_value = (
            static_value
            + base_total * float(stats.get(f"runtime_{stat}_percent_bonus", 0.0))
            + runtime_flat
        )
        stats[f"base_{stat}_total"] = base_total
        stats[f"static_{stat}"] = static_value
        stats[f"effective_{stat}"] = effective_value
        stats[f"runtime_{stat}_flat_bonus"] = runtime_flat
        reference = stats.get(f"final_{stat}_reference")
        stats[f"{stat}_reference_delta"] = None
        stats[f"{stat}_reference_delta_percent"] = None
        if reference not in (None, 0):
            stats[f"{stat}_reference_delta"] = static_value - float(reference)
            stats[f"{stat}_reference_delta_percent"] = stats[f"{stat}_reference_delta"] / float(reference)

    stats["base_attack_total"] = stats["base_atk_total"]
    stats["static_attack"] = stats["static_atk"]
    stats["effective_attack"] = stats["effective_atk"]
    stats["final_attack_reference"] = stats.get("final_atk_reference")
    stats["attack_reference_delta"] = stats.get("atk_reference_delta")
    stats["attack_reference_delta_percent"] = stats.get("atk_reference_delta_percent")
    stats["runtime_flat_atk_bonus"] = stats["runtime_atk_flat_bonus"]
    stats["atk_percent"] = float(stats.get("static_atk_percent", 0.0)) + float(stats.get("runtime_atk_percent_bonus", 0.0))
    stats["flat_atk"] = float(stats.get("static_flat_atk", 0.0)) + float(stats.get("runtime_atk_flat_bonus", 0.0))


def _recalculate_attack_stats(stats: dict[str, Any]) -> None:
    _recalculate_scaling_stats(stats)


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


def buff_applies_to_character(buff: BuffData, active: ActiveBuff, character: CharacterData, state: CombatState) -> bool:
    return _buff_applies(buff, active, character, state)


def get_active_buffs_for_character(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
    *,
    time_offset: float = 0.0,
    force_active_buff_ids: set[str] | None = None,
) -> list[tuple[ActiveBuff, BuffData]]:
    active_pairs: list[tuple[ActiveBuff, BuffData]] = []
    forced_ids = force_active_buff_ids or set()
    for active in state.active_buffs:
        if active.remaining_duration <= time_offset and active.buff_id not in forced_ids:
            continue
        buff = buffs[active.buff_id]
        if not _buff_applies(buff, active, character, state):
            continue
        active_pairs.append((active, buff))
    return active_pairs


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
    force_active_buff_ids: set[str] | None = None,
) -> list[tuple[ActiveBuff, BuffData]]:
    character = CharacterData(
        id=actor_character_id,
        name=actor_character_id,
        resonance_energy=0.0,
        concerto_energy=0.0,
    )
    active_pairs: list[tuple[ActiveBuff, BuffData]] = []
    forced_ids = force_active_buff_ids or set()
    for active in state.active_buffs:
        if active.remaining_duration <= time_offset and active.buff_id not in forced_ids:
            continue
        buff = buffs[active.buff_id]
        if not _buff_applies(buff, active, character, state):
            continue
        if not _tags_match(buff, action):
            continue
        active_pairs.append((active, buff))
    return active_pairs


def _dynamic_value(active: ActiveBuff, buff: BuffData) -> float:
    return float((active.metadata or {}).get("dynamic_value", buff.value) or 0.0)


def effective_damage_amp_contribution(
    active: ActiveBuff,
    buff: BuffData,
    *,
    action: Any | None = None,
    category: str | None = None,
) -> float:
    damage_amp_modifiers = dict(buff.damage_amp_modifiers or {})
    if damage_amp_modifiers:
        if category is not None:
            return float(damage_amp_modifiers.get(category, 0.0) or 0.0)
        contribution = float(damage_amp_modifiers.get("all", 0.0) or 0.0)
        action_categories = set(getattr(action, "tags", []) or [])
        damage_bonus_category = getattr(action, "damage_bonus_category", None)
        if damage_bonus_category:
            action_categories.add(str(damage_bonus_category))
        for tag in action_categories:
            contribution += float(damage_amp_modifiers.get(tag, 0.0) or 0.0)
        return contribution
    if buff.modifier_type == "damage_amp":
        return _dynamic_value(active, buff)
    return 0.0


def effective_atk_percent_contribution(active: ActiveBuff, buff: BuffData) -> float:
    metadata = active.metadata or {}
    if buff.modifier_type == "attack" and "dynamic_value" in metadata:
        return float(metadata.get("dynamic_value") or 0.0)
    explicit_atk_percent = float((buff.stat_modifiers or {}).get("atk_percent", 0.0) or 0.0)
    if explicit_atk_percent != 0.0:
        return explicit_atk_percent
    if buff.modifier_type == "attack":
        return float(buff.value or 0.0)
    return 0.0


def damage_amp_for_action(
    actor_character_id: str,
    action: Any,
    state: CombatState,
    buffs: dict[str, BuffData],
    *,
    time_offset: float = 0.0,
    force_active_buff_ids: set[str] | None = None,
) -> float:
    damage_amp = 0.0
    for active, buff in get_active_buffs_for_action(
        actor_character_id,
        action,
        state,
        buffs,
        time_offset=time_offset,
        force_active_buff_ids=force_active_buff_ids,
    ):
        damage_amp += effective_damage_amp_contribution(active, buff, action=action)
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


def collect_runtime_def_percent_bonus(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
    time_offset: float = 0.0,
) -> float:
    return float(buffed_combat_stats(character, state, buffs, time_offset=time_offset)["runtime_def_percent_bonus"])


def collect_runtime_flat_def_bonus(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
    time_offset: float = 0.0,
) -> float:
    return float(buffed_combat_stats(character, state, buffs, time_offset=time_offset)["runtime_def_flat_bonus"])


def support_stat_context(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
    *,
    time_offset: float = 0.0,
    force_active_buff_ids: set[str] | None = None,
) -> dict[str, Any]:
    support_stats = normalize_support_stats(character.support_stats)
    base_off_tune = float(support_stats.get("off_tune_buildup_rate", 1.0) or 1.0)
    base_tune_break_boost = float(support_stats.get("tune_break_boost", 0.0) or 0.0)
    runtime_bonus = 0.0
    tune_break_boost_bonus = 0.0
    syntony_bonus = 0.0
    c2_bonus_active = False
    active_support_buffs: list[str] = []
    forced_ids = force_active_buff_ids or set()

    for active in state.active_buffs:
        if active.remaining_duration <= time_offset and active.buff_id not in forced_ids:
            continue
        buff = buffs.get(active.buff_id)
        if buff is None:
            continue
        if not _buff_applies(buff, active, character, state):
            continue
        for stat_name, stat_value in buff.support_stat_modifiers.items():
            active_support_buffs.append(buff.id)
            value = float(active.metadata.get("dynamic_support_value", stat_value))
            if stat_name == "off_tune_buildup_rate_add":
                runtime_bonus += value
                if buff.id in {
                    "mornye_syntony_field_off_tune_buildup_rate",
                    "mornye_high_syntony_field_off_tune_buildup_rate",
                }:
                    syntony_bonus += value
                    c2_bonus_active = c2_bonus_active or bool(active.metadata.get("c2_off_tune_bonus_active", False))
            elif stat_name == "tune_break_boost_points_add":
                tune_break_boost_bonus += value

    return {
        "support_stats": support_stats,
        "base_off_tune_buildup_rate": base_off_tune,
        "runtime_off_tune_buildup_rate_bonus": runtime_bonus,
        "current_off_tune_buildup_rate": base_off_tune + runtime_bonus,
        "base_tune_break_boost_points": base_tune_break_boost,
        "runtime_tune_break_boost_points_bonus": tune_break_boost_bonus,
        "current_tune_break_boost_points": base_tune_break_boost + tune_break_boost_bonus,
        "syntony_field_off_tune_bonus_active": syntony_bonus > 0.0,
        "syntony_field_off_tune_bonus_value": syntony_bonus,
        "c2_off_tune_bonus_active": c2_bonus_active,
        "active_support_buff_ids": active_support_buffs,
    }


def buffed_combat_stats(
    character: CharacterData,
    state: CombatState,
    buffs: dict[str, BuffData],
    time_offset: float = 0.0,
    force_active_buff_ids: set[str] | None = None,
) -> dict[str, float]:
    stats = {
        **stat_component_log_fields(character),
        **support_stat_context(
            character,
            state,
            buffs,
            time_offset=time_offset,
            force_active_buff_ids=force_active_buff_ids,
        ),
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
        "damage_bonus_by_element_buff": {},
        "echo_set_damage_bonus_by_element": {},
        "crit_rate_before_buffs": character.crit_rate,
        "crit_damage_before_buffs": character.crit_damage,
        "runtime_crit_damage_bonus": 0.0,
        "starfield_calibrator_party_crit_damage_active": False,
        "starfield_calibrator_party_crit_damage_bonus": 0.0,
        "high_syntony_field_def_bonus_active": False,
        "high_syntony_field_def_percent_bonus": 0.0,
        "high_syntony_field_off_tune_inherited": False,
        "high_syntony_field_heal_proxy_active": False,
        "high_syntony_field_healing_multiplier_bonus": 0.0,
        "high_syntony_field_healing_multiplier_metadata_only": True,
        "halo_atk_buff_does_not_affect_mornye_def_damage": False,
        "halo_of_starry_radiance_5set_active": False,
        "halo_of_starry_radiance_5set_atk_percent_bonus": 0.0,
        "static_mist_incoming_atk_buff_active": False,
        "static_mist_incoming_atk_percent_bonus": 0.0,
        "pact_neonlight_incoming_atk_buff_active": False,
        "pact_neonlight_incoming_atk_percent_bonus": 0.0,
        "hyvatia_incoming_all_attribute_buff_active": False,
        "hyvatia_incoming_all_attribute_damage_bonus": 0.0,
    }
    active_buff_names: list[str] = []
    forced_ids = force_active_buff_ids or set()

    for active in state.active_buffs:
        if active.remaining_duration <= time_offset and active.buff_id not in forced_ids:
            continue
        buff = buffs[active.buff_id]
        if not _buff_applies(buff, active, character, state):
            continue
        buff_value = _dynamic_value(active, buff)
        atk_percent_contribution = effective_atk_percent_contribution(active, buff)
        active_buff_names.append(buff.id)
        if buff.id == "mornye_halo_of_starry_radiance_5set":
            stats["halo_of_starry_radiance_5set_active"] = True
            stats["halo_of_starry_radiance_5set_atk_percent_bonus"] = max(
                float(stats.get("halo_of_starry_radiance_5set_atk_percent_bonus", 0.0)),
                atk_percent_contribution,
            )
        if buff.id == "static_mist_incoming_atk":
            stats["static_mist_incoming_atk_buff_active"] = True
            stats["static_mist_incoming_atk_percent_bonus"] = max(
                float(stats.get("static_mist_incoming_atk_percent_bonus", 0.0)),
                atk_percent_contribution,
            )
        if buff.id == "pact_neonlight_incoming_atk":
            stats["pact_neonlight_incoming_atk_buff_active"] = True
            stats["pact_neonlight_incoming_atk_percent_bonus"] = max(
                float(stats.get("pact_neonlight_incoming_atk_percent_bonus", 0.0)),
                atk_percent_contribution,
            )
        if buff.id == "hyvatia_incoming_all_attribute_damage_bonus":
            stats["hyvatia_incoming_all_attribute_buff_active"] = True
            stats["hyvatia_incoming_all_attribute_damage_bonus"] = max(
                float(stats.get("hyvatia_incoming_all_attribute_damage_bonus", 0.0)),
                buff_value,
            )
        if buff.id == "mornye_high_syntony_field_def_bonus":
            stats["high_syntony_field_def_bonus_active"] = True
            stats["high_syntony_field_def_percent_bonus"] = max(
                float(stats.get("high_syntony_field_def_percent_bonus", 0.0)),
                float(buff.stat_modifiers.get("def_percent", 0.0)),
            )
        if buff.id == "mornye_high_syntony_field_off_tune_buildup_rate":
            stats["high_syntony_field_off_tune_inherited"] = True
            stats["high_syntony_field_healing_multiplier_bonus"] = 0.40
        if buff.id == "starfield_calibrator_party_crit_damage":
            stats["starfield_calibrator_party_crit_damage_active"] = True
            stats["starfield_calibrator_party_crit_damage_bonus"] = max(
                float(stats.get("starfield_calibrator_party_crit_damage_bonus", 0.0)),
                float(active.metadata.get("dynamic_value", buff.stat_modifiers.get("crit_damage", 0.0)) or 0.0),
            )
        if atk_percent_contribution:
            stats["runtime_atk_percent_bonus"] += atk_percent_contribution
        if buff.modifier_type == "attack":
            pass
        elif buff.modifier_type == "damage_bonus":
            stats["dmg_bonus"] += buff_value
            stats["damage_bonus_buff"] += buff_value
        elif buff.modifier_type == "boost":
            stats["boost"] += buff_value
        elif buff.modifier_type == "dmg_taken":
            stats["dmg_taken"] += buff_value
        for stat_name, stat_value in buff.stat_modifiers.items():
            if stat_name == "atk_percent":
                continue
            elif stat_name == "flat_atk":
                stats["runtime_atk_flat_bonus"] += stat_value
                stats["runtime_flat_atk_bonus"] += stat_value
            elif stat_name == "def_percent":
                stats["runtime_def_percent_bonus"] += stat_value
            elif stat_name == "flat_def":
                stats["runtime_def_flat_bonus"] += stat_value
            elif stat_name == "hp_percent":
                stats["runtime_hp_percent_bonus"] += stat_value
            elif stat_name == "flat_hp":
                stats["runtime_hp_flat_bonus"] += stat_value
            elif stat_name == "crit_damage":
                value = float(active.metadata.get("dynamic_value", stat_value))
                stats["crit_damage"] += value
                stats["runtime_crit_damage_bonus"] += value
            elif stat_name in stats:
                stats[stat_name] += stat_value
        if buff.damage_bonus_by_element:
            for element, element_bonus in buff.damage_bonus_by_element.items():
                element_key = str(element).strip().lower()
                stats["damage_bonus_by_element_buff"][element_key] = (
                    stats["damage_bonus_by_element_buff"].get(element_key, 0.0) + float(element_bonus)
                )
                if buff.metadata.get("source_type") == "echo_set":
                    stats["echo_set_damage_bonus_by_element"][element_key] = (
                        stats["echo_set_damage_bonus_by_element"].get(element_key, 0.0) + float(element_bonus)
                    )

    _recalculate_scaling_stats(stats)
    stats.update(support_stat_log_fields(stats))
    stats["crit_rate_after_buffs"] = stats["crit_rate"]
    stats["crit_damage_after_buffs"] = stats["crit_damage"]
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
