from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simulator.action_start_snapshot import ActionStartEffectSnapshot
from simulator.buff_system import apply_buff, get_active_buffs_for_action
from simulator.models import ActionData, BuffData, CharacterData, CombatState
from simulator.resource_system import add_concerto_energy, sync_concerto_state


STARFIELD_CALIBRATOR_BUFF_ID = "starfield_calibrator_party_crit_damage"
SUPPORTED_TRIGGER_EVENT_NAMES = {
    "resonance_skill_cast",
    "resonance_liberation_cast",
    "intro_cast",
    "outro_cast",
    "team_heal",
    "damage_dealt",
    "tune_break_dealt",
    "mechanic_event_emitted",
    "crit_hit",
    "swap_in",
    "swap_out",
}
SUPPORTED_EFFECT_TYPES = {
    "resource_restore",
    "stat_buff",
    "party_stat_buff",
    "damage_bonus_buff",
    "conditional_penetration_buff",
    "damage_taken_amp",
    "cooldown_gated_effect",
    "stackable_effect",
}


def load_weapon_definition(data_dir: Path | str) -> dict[str, Any]:
    path = Path(data_dir) / "weapons.json"
    if not path.exists():
        return {
            "schema_version": 1,
            "supported_trigger_event_names": sorted(SUPPORTED_TRIGGER_EVENT_NAMES),
            "supported_effect_types": sorted(SUPPORTED_EFFECT_TYPES),
            "weapons": {},
        }
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def get_character_weapon(character: CharacterData | None) -> dict[str, Any]:
    if character is None:
        return {}
    weapon = dict(character.weapon or {})
    if not weapon.get("weapon_id"):
        return {}
    return weapon


def active_weapons_for_characters(characters: dict[str, CharacterData]) -> dict[str, dict[str, Any]]:
    return {
        character_id: get_character_weapon(character)
        for character_id, character in characters.items()
        if get_character_weapon(character)
    }


def weapon_effects_enabled(characters: dict[str, CharacterData], weapon_definitions: dict[str, Any]) -> bool:
    defined = weapon_definitions.get("weapons") or {}
    return any(weapon.get("weapon_id") in defined for weapon in active_weapons_for_characters(characters).values())


def process_weapon_effects_before_or_after_action(
    *,
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    weapon_definitions: dict[str, Any],
    application_time: float,
) -> dict[str, Any]:
    trigger = _trigger_for_action(action)
    if trigger is None or action.character_id is None:
        return weapon_effect_base_log()
    return apply_weapon_resource_effects(
        trigger=trigger,
        source_character_id=action.character_id,
        state=state,
        characters=characters,
        buffs=buffs,
        weapon_definitions=weapon_definitions,
        application_time=application_time,
        event_source=f"action:{action.id}",
    )


def apply_weapon_resource_effects(
    *,
    trigger: str,
    source_character_id: str,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    weapon_definitions: dict[str, Any],
    application_time: float,
    event_source: str,
) -> dict[str, Any]:
    del buffs
    log = weapon_effect_base_log()
    if trigger not in SUPPORTED_TRIGGER_EVENT_NAMES:
        return log
    character = characters.get(source_character_id)
    weapon = get_character_weapon(character)
    weapon_def = _weapon_definition(weapon_definitions, weapon)
    if not weapon_def:
        return log

    for effect_id, effect in (weapon_def.get("effects") or {}).items():
        if effect.get("trigger") != trigger or effect.get("effect_type") != "resource_restore":
            continue
        resource = str(effect.get("resource") or "")
        if resource != "concerto_energy":
            continue

        weapon_id = str(weapon_def.get("id") or weapon.get("weapon_id"))
        rank = _weapon_rank(weapon)
        cooldown_key = weapon_effect_cooldown_key(source_character_id, weapon_id, effect_id)
        cooldown_remaining = float(state.weapon_effect_cooldowns.get(cooldown_key, 0.0) or 0.0)
        base = _effect_log_base(
            effect_id=effect_id,
            effect=effect,
            weapon=weapon,
            weapon_def=weapon_def,
            source_character_id=source_character_id,
            application_time=application_time,
            event_source=event_source,
        )
        base["weapon_effect_resource"] = resource
        base["weapon_effect_cooldown_remaining"] = cooldown_remaining
        if cooldown_remaining > 1e-9:
            base["weapon_effect_cooldown_blocked"] = True
            state.weapon_effect_cooldown_blocked_counts[cooldown_key] = (
                state.weapon_effect_cooldown_blocked_counts.get(cooldown_key, 0) + 1
            )
            state.weapon_effect_logs.append(base)
            _merge_weapon_log(log, base)
            continue

        amount = _rank_value(weapon_def, rank, str(effect.get("rank_value_key") or ""))
        character_state = sync_concerto_state(state, source_character_id)
        before, restored, after, ready, wasted = add_concerto_energy(character_state, amount)
        state.concerto_energy[source_character_id] = after
        state.wasted_concerto_energy[source_character_id] = (
            state.wasted_concerto_energy.get(source_character_id, 0.0) + wasted
        )
        cooldown_seconds = float(effect.get("cooldown_seconds", 0.0) or 0.0)
        if cooldown_seconds > 0.0:
            state.weapon_effect_cooldowns[cooldown_key] = cooldown_seconds
        state.weapon_effect_trigger_counts[cooldown_key] = state.weapon_effect_trigger_counts.get(cooldown_key, 0) + 1
        if weapon_id == "starfield_calibrator":
            state.starfield_calibrator_concerto_restored_total += restored
        base.update(
            {
                "weapon_effect_triggered": restored > 0.0 or amount > 0.0,
                "concerto_energy_before_weapon_effect": before,
                "concerto_energy_restored_by_weapon": restored,
                "concerto_energy_after_weapon_effect": after,
                "concerto_energy_wasted_by_weapon": wasted,
                "concerto_ready_after_weapon_effect": ready,
                "weapon_effect_cooldown_seconds": cooldown_seconds,
                "weapon_effect_cooldown_remaining": cooldown_seconds,
            }
        )
        state.weapon_effect_logs.append(base)
        _merge_weapon_log(log, base)
    return log


def apply_weapon_buff_effects(
    *,
    trigger: str,
    source_character_id: str,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    weapon_definitions: dict[str, Any],
    application_time: float,
    event_source: str,
) -> dict[str, Any]:
    log = weapon_effect_base_log()
    if trigger not in SUPPORTED_TRIGGER_EVENT_NAMES:
        return log
    character = characters.get(source_character_id)
    weapon = get_character_weapon(character)
    weapon_def = _weapon_definition(weapon_definitions, weapon)
    if not weapon_def:
        return log

    for effect_id, effect in (weapon_def.get("effects") or {}).items():
        effect_type = effect.get("effect_type")
        if effect.get("trigger") != trigger or effect_type not in {"stat_buff", "party_stat_buff"}:
            continue
        buff_id = str(effect.get("buff_id") or "")
        buff = buffs.get(buff_id)
        stat = str(effect.get("stat") or "")
        if buff is None or not stat:
            continue

        weapon_id = str(weapon_def.get("id") or weapon.get("weapon_id"))
        rank = _weapon_rank(weapon)
        value = _rank_value(weapon_def, rank, str(effect.get("rank_value_key") or ""))
        runtime_buff = buff.model_copy(deep=True)
        runtime_buff.duration = float(effect.get("duration_seconds", runtime_buff.duration) or runtime_buff.duration)
        runtime_buff.max_stacks = int(effect.get("max_stacks", runtime_buff.max_stacks) or runtime_buff.max_stacks)
        runtime_buff.stacking_rule = str(effect.get("stacking_rule") or runtime_buff.stacking_rule)
        runtime_buff.value = value
        runtime_buff.source_character_id = source_character_id
        runtime_buff.stat_modifiers = {**runtime_buff.stat_modifiers, stat: value}
        runtime_buff.metadata = {
            **runtime_buff.metadata,
            "dynamic_value": value,
            "weapon_id": weapon_id,
            "weapon_rank": rank,
            "weapon_effect_id": effect_id,
            "weapon_effect_type": effect_type,
            "trigger": trigger,
            "event_source": event_source,
            "weapon_effect_source_status": weapon_def.get(
                "source_status",
                runtime_buff.metadata.get("weapon_effect_source_status", runtime_buff.metadata.get("source_status")),
            ),
        }
        runtime_buff.metadata.pop("source_status", None)
        was_active = _active_buff_exists(state, runtime_buff.id)
        before_values = _party_stat_values(characters, state, buffs, stat)
        apply_buff(state, runtime_buff, source_character_id)
        after_values = _party_stat_values(characters, state, buffs, stat)
        key = weapon_effect_cooldown_key(source_character_id, weapon_id, effect_id)
        state.weapon_effect_trigger_counts[key] = state.weapon_effect_trigger_counts.get(key, 0) + 1
        _record_weapon_buff_window(state, runtime_buff.id, source_character_id, application_time, runtime_buff.duration)
        base = _effect_log_base(
            effect_id=effect_id,
            effect=effect,
            weapon=weapon,
            weapon_def=weapon_def,
            source_character_id=source_character_id,
            application_time=application_time,
            event_source=event_source,
        )
        base.update(
            {
                "weapon_effect_triggered": True,
                "weapon_effect_buff_refreshed": was_active,
                "weapon_effect_duration_seconds": runtime_buff.duration,
                "team_heal_event_triggered": trigger == "team_heal",
                "starfield_calibrator_party_crit_damage_active": runtime_buff.id == STARFIELD_CALIBRATOR_BUFF_ID,
                "starfield_calibrator_party_crit_damage_bonus": value
                if runtime_buff.id == STARFIELD_CALIBRATOR_BUFF_ID
                else 0.0,
                "crit_damage_before_weapon_buffs": before_values,
                "crit_damage_after_weapon_buffs": after_values,
                "active_buff_ids": [active.buff_id for active in state.active_buffs if active.remaining_duration > 0.0],
            }
        )
        state.weapon_effect_logs.append(base)
        _merge_weapon_log(log, base)
    return log


def apply_weapon_mechanic_event_effects(
    *,
    emitted_event_tags: list[str],
    source_character_id: str,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    weapon_definitions: dict[str, Any],
    application_time: float,
    event_source: str,
) -> dict[str, Any]:
    log = weapon_effect_base_log()
    if not emitted_event_tags:
        return log
    character = characters.get(source_character_id)
    weapon = get_character_weapon(character)
    weapon_def = _weapon_definition(weapon_definitions, weapon)
    if not weapon_def:
        return log

    emitted = {str(tag) for tag in emitted_event_tags}
    for effect_id, effect in (weapon_def.get("effects") or {}).items():
        if effect.get("trigger") != "mechanic_event_emitted":
            continue
        if effect.get("effect_type") != "conditional_penetration_buff":
            continue
        trigger_tags = {str(tag) for tag in effect.get("trigger_event_tags", [])}
        matched_tags = sorted(emitted.intersection(trigger_tags))
        if not matched_tags:
            continue
        buff_id = str(effect.get("buff_id") or "")
        buff = buffs.get(buff_id)
        if buff is None:
            continue

        weapon_id = str(weapon_def.get("id") or weapon.get("weapon_id"))
        rank = _weapon_rank(weapon)
        rank_values = weapon_def.get("rank_values") or {}
        values = rank_values.get(str(rank)) or {}
        def_ignore_bonus = float(values.get("resonance_liberation_def_ignore", 0.0) or 0.0)
        fusion_res_ignore_bonus = float(values.get("resonance_liberation_fusion_res_ignore", 0.0) or 0.0)

        runtime_buff = buff.model_copy(deep=True)
        runtime_buff.duration = float(effect.get("duration_seconds", runtime_buff.duration) or runtime_buff.duration)
        runtime_buff.max_stacks = int(effect.get("max_stacks", runtime_buff.max_stacks) or runtime_buff.max_stacks)
        runtime_buff.stacking_rule = str(effect.get("stacking_rule") or runtime_buff.stacking_rule)
        runtime_buff.source_character_id = source_character_id
        runtime_buff.metadata = {
            **runtime_buff.metadata,
            "dynamic_def_ignore": def_ignore_bonus,
            "dynamic_fusion_res_ignore": fusion_res_ignore_bonus,
            "dynamic_value": def_ignore_bonus,
            "weapon_id": weapon_id,
            "weapon_rank": rank,
            "weapon_effect_id": effect_id,
            "weapon_effect_type": effect.get("effect_type"),
            "trigger": "mechanic_event_emitted",
            "trigger_event_tags": matched_tags,
            "event_source": event_source,
            "damage_bonus_category_filter": effect.get("damage_bonus_category_filter"),
            "element_filter_for_res_ignore": effect.get("element_filter_for_res_ignore"),
            "weapon_effect_source_status": weapon_def.get(
                "source_status",
                runtime_buff.metadata.get("weapon_effect_source_status", runtime_buff.metadata.get("source_status")),
            ),
        }
        runtime_buff.metadata.pop("source_status", None)
        was_active = _active_buff_exists(state, runtime_buff.id)
        apply_buff(state, runtime_buff, source_character_id)
        key = weapon_effect_cooldown_key(source_character_id, weapon_id, effect_id)
        state.weapon_effect_trigger_counts[key] = state.weapon_effect_trigger_counts.get(key, 0) + 1
        _record_weapon_buff_window(state, runtime_buff.id, source_character_id, application_time, runtime_buff.duration)
        base = _effect_log_base(
            effect_id=effect_id,
            effect=effect,
            weapon=weapon,
            weapon_def=weapon_def,
            source_character_id=source_character_id,
            application_time=application_time,
            event_source=event_source,
        )
        base.update(
            {
                "weapon_effect_triggered": True,
                "weapon_effect_buff_refreshed": was_active,
                "weapon_effect_duration_seconds": runtime_buff.duration,
                "everbright_polestar_liberation_penetration_active": True,
                "everbright_polestar_liberation_penetration_remaining": runtime_buff.duration,
                "everbright_polestar_def_ignore_bonus": def_ignore_bonus,
                "everbright_polestar_fusion_res_ignore_bonus": fusion_res_ignore_bonus,
                "everbright_polestar_trigger_event_tags": matched_tags,
                "everbright_polestar_triggered_this_action": True,
                "everbright_polestar_buff_refreshed": was_active,
                "active_buff_ids": [active.buff_id for active in state.active_buffs if active.remaining_duration > 0.0],
            }
        )
        state.weapon_effect_logs.append(base)
        _merge_weapon_log(log, base)
    return log


def weapon_runtime_damage_effects(
    *,
    character: CharacterData,
    action: ActionData,
    state: CombatState,
    buffs: dict[str, BuffData],
    weapon_definitions: dict[str, Any],
    damage_element: str,
    damage_bonus_category: str,
    hit_damage_category: str,
    time_offset: float = 0.0,
    action_start_snapshot: ActionStartEffectSnapshot | None = None,
) -> dict[str, Any]:
    weapon = get_character_weapon(character)
    weapon_def = _weapon_definition(weapon_definitions, weapon)
    base = {
        "runtime_element_bonus_by_element": {},
        "runtime_all_attribute_damage_bonus": 0.0,
        "everbright_polestar_all_attribute_bonus_active": False,
        "everbright_polestar_all_attribute_damage_bonus": 0.0,
        "everbright_polestar_liberation_penetration_active": False,
        "everbright_polestar_liberation_penetration_remaining": 0.0,
        "everbright_polestar_def_ignore_bonus": 0.0,
        "everbright_polestar_fusion_res_ignore_bonus": 0.0,
        "weapon_effect_id": None,
        "weapon_effect_source_status": None,
        "weapon_effects_enabled": bool(weapon_def),
    }
    if not weapon_def:
        return base

    weapon_id = str(weapon_def.get("id") or weapon.get("weapon_id"))
    rank = _weapon_rank(weapon)
    element_key = str(damage_element or "generic").strip().lower() or "generic"
    for effect_id, effect in (weapon_def.get("effects") or {}).items():
        if effect.get("trigger") != "always_active":
            continue
        if effect.get("effect_type") != "damage_bonus_buff":
            continue
        if effect.get("damage_bonus_scope") != "all_attribute":
            continue
        if hit_damage_category != "normal" and not bool(effect.get("applies_to_tune_damage", False)):
            continue
        value = _rank_value(weapon_def, rank, str(effect.get("rank_value_key") or ""))
        if value <= 0.0:
            continue
        base["runtime_element_bonus_by_element"][element_key] = (
            base["runtime_element_bonus_by_element"].get(element_key, 0.0) + value
        )
        base["runtime_all_attribute_damage_bonus"] += value
        base["weapon_effect_id"] = effect_id
        base["weapon_effect_source_status"] = weapon_def.get("source_status")
        if weapon_id == "everbright_polestar":
            base["everbright_polestar_all_attribute_bonus_active"] = True
            base["everbright_polestar_all_attribute_damage_bonus"] += value

    if hit_damage_category != "normal":
        return base

    for active, buff in get_active_buffs_for_action(
        character.id,
        action,
        state,
        buffs,
        time_offset=time_offset,
        force_active_buff_ids=set(action_start_snapshot.active_buff_ids) if action_start_snapshot is not None else None,
    ):
        if buff.metadata.get("source_type") != "weapon":
            continue
        if buff.metadata.get("weapon_id") != weapon_id:
            continue
        category_filter = str(
            active.metadata.get("damage_bonus_category_filter")
            or buff.metadata.get("applies_to_damage_bonus_category")
            or ""
        )
        if category_filter and damage_bonus_category != category_filter:
            continue
        def_ignore_bonus = float(active.metadata.get("dynamic_def_ignore", 0.0) or 0.0)
        res_ignore_bonus = 0.0
        element_filter = str(active.metadata.get("element_filter_for_res_ignore") or "").strip().lower()
        if element_filter and element_key == element_filter:
            res_ignore_bonus = float(active.metadata.get("dynamic_fusion_res_ignore", 0.0) or 0.0)
        base["everbright_polestar_liberation_penetration_active"] = True
        snapshot_remaining = (
            action_start_snapshot.buff_remaining(active.buff_id)
            if action_start_snapshot is not None and action_start_snapshot.buff_active(active.buff_id)
            else None
        )
        base["everbright_polestar_liberation_penetration_remaining"] = max(
            float(base["everbright_polestar_liberation_penetration_remaining"]),
            _remaining_for_damage_context(
                active_remaining=float(active.remaining_duration),
                time_offset=time_offset,
                snapshot_remaining=snapshot_remaining,
            ),
        )
        if weapon_id == "everbright_polestar":
            base["everbright_polestar_def_ignore_bonus"] = max(
                float(base["everbright_polestar_def_ignore_bonus"]),
                def_ignore_bonus,
            )
            base["everbright_polestar_fusion_res_ignore_bonus"] = max(
                float(base["everbright_polestar_fusion_res_ignore_bonus"]),
                res_ignore_bonus,
            )
    return base


def advance_weapon_effect_cooldowns(state: CombatState, elapsed: float) -> None:
    elapsed = max(0.0, float(elapsed or 0.0))
    if elapsed <= 0.0:
        return
    for key, remaining in list(state.weapon_effect_cooldowns.items()):
        updated = max(0.0, float(remaining or 0.0) - elapsed)
        if updated > 0.0:
            state.weapon_effect_cooldowns[key] = updated
        else:
            del state.weapon_effect_cooldowns[key]


def _remaining_for_damage_context(
    *,
    active_remaining: float,
    time_offset: float,
    snapshot_remaining: float | None,
) -> float:
    if snapshot_remaining is not None:
        return max(0.0, snapshot_remaining)
    return max(0.0, active_remaining - time_offset)


def weapon_effect_uptime_seconds(state: CombatState, buff_id: str, combat_time: float | None = None) -> float:
    total = 0.0
    limit = combat_time if combat_time is not None else None
    for window in state.weapon_effect_buff_windows:
        if window.get("buff_id") != buff_id:
            continue
        start = float(window.get("start_time", 0.0))
        end = float(window.get("end_time", start))
        if limit is not None:
            end = min(end, float(limit))
        total += max(0.0, end - start)
    return total


def weapon_effect_base_log() -> dict[str, Any]:
    return {
        "weapon_effects_enabled": False,
        "weapon_effect_triggered": False,
        "weapon_effect_logs": [],
        "weapon_id": None,
        "weapon_rank": 0,
        "weapon_effect_id": None,
        "weapon_effect_type": None,
        "weapon_effect_resource": None,
        "weapon_effect_cooldown_seconds": 0.0,
        "weapon_effect_cooldown_remaining": 0.0,
        "weapon_effect_cooldown_blocked": False,
        "concerto_energy_before_weapon_effect": 0.0,
        "concerto_energy_restored_by_weapon": 0.0,
        "concerto_energy_after_weapon_effect": 0.0,
        "concerto_energy_wasted_by_weapon": 0.0,
        "starfield_calibrator_party_crit_damage_active": False,
        "starfield_calibrator_party_crit_damage_bonus": 0.0,
    }


def weapon_effect_cooldown_key(character_id: str, weapon_id: str, effect_id: str) -> str:
    return f"{character_id}:{weapon_id}:{effect_id}"


def _trigger_for_action(action: ActionData) -> str | None:
    if action.action_type == "resonance_skill" or action.damage_bonus_category == "resonance_skill":
        return "resonance_skill_cast"
    if action.action_type == "resonance_liberation":
        return "resonance_liberation_cast"
    if action.action_type == "swap":
        return "swap_in"
    return None


def _weapon_definition(weapon_definitions: dict[str, Any], weapon: dict[str, Any]) -> dict[str, Any]:
    weapon_id = str(weapon.get("weapon_id") or "")
    if not weapon_id:
        return {}
    return dict((weapon_definitions.get("weapons") or {}).get(weapon_id) or {})


def _weapon_rank(weapon: dict[str, Any]) -> int:
    return min(5, max(1, int(weapon.get("rank", 1) or 1)))


def _rank_value(weapon_def: dict[str, Any], rank: int, key: str) -> float:
    if not key:
        return 0.0
    rank_values = weapon_def.get("rank_values") or {}
    return float((rank_values.get(str(rank)) or {}).get(key, 0.0) or 0.0)


def _effect_log_base(
    *,
    effect_id: str,
    effect: dict[str, Any],
    weapon: dict[str, Any],
    weapon_def: dict[str, Any],
    source_character_id: str,
    application_time: float,
    event_source: str,
) -> dict[str, Any]:
    rank = _weapon_rank(weapon)
    return {
        "weapon_effects_enabled": True,
        "weapon_effect_triggered": False,
        "weapon_id": str(weapon_def.get("id") or weapon.get("weapon_id")),
        "weapon_rank": rank,
        "weapon_type": str(weapon_def.get("weapon_type") or weapon.get("weapon_type") or ""),
        "weapon_effect_id": effect_id,
        "weapon_effect_type": str(effect.get("effect_type") or ""),
        "weapon_effect_trigger": str(effect.get("trigger") or ""),
        "source_character_id": source_character_id,
        "weapon_effect_source_status": weapon_def.get("source_status"),
        "weapon_effect_application_time": application_time,
        "weapon_effect_event_source": event_source,
        "weapon_effect_cooldown_seconds": float(effect.get("cooldown_seconds", 0.0) or 0.0),
        "weapon_effect_cooldown_blocked": False,
    }


def _merge_weapon_log(merged: dict[str, Any], log: dict[str, Any]) -> None:
    merged["weapon_effects_enabled"] = bool(merged.get("weapon_effects_enabled") or log.get("weapon_effects_enabled"))
    merged["weapon_effect_triggered"] = bool(merged.get("weapon_effect_triggered") or log.get("weapon_effect_triggered"))
    merged["weapon_effect_cooldown_blocked"] = bool(
        merged.get("weapon_effect_cooldown_blocked") or log.get("weapon_effect_cooldown_blocked")
    )
    merged["weapon_effect_logs"] = [*merged.get("weapon_effect_logs", []), dict(log)]
    for key, value in log.items():
        if value in (None, "", [], {}) and key in merged:
            continue
        if key in {"weapon_effect_triggered", "weapon_effects_enabled", "weapon_effect_cooldown_blocked"}:
            continue
        merged[key] = value


def _active_buff_exists(state: CombatState, buff_id: str) -> bool:
    return any(active.buff_id == buff_id and active.remaining_duration > 0.0 for active in state.active_buffs)


def _record_weapon_buff_window(
    state: CombatState,
    buff_id: str,
    character_id: str | None,
    application_time: float,
    duration: float,
) -> None:
    end_time = application_time + duration
    for window in reversed(state.weapon_effect_buff_windows):
        if window.get("buff_id") == buff_id and window.get("character_id") == character_id:
            if float(window.get("end_time", 0.0)) >= application_time - 1e-9:
                window["end_time"] = end_time
                window["duration"] = max(0.0, end_time - float(window.get("start_time", application_time)))
                return
    state.weapon_effect_buff_windows.append(
        {
            "buff_id": buff_id,
            "character_id": character_id,
            "start_time": application_time,
            "end_time": end_time,
            "duration": duration,
        }
    )


def _party_stat_values(
    characters: dict[str, CharacterData],
    state: CombatState,
    buffs: dict[str, BuffData],
    stat: str,
) -> dict[str, float]:
    if stat != "crit_damage":
        return {}
    from simulator.buff_system import buffed_combat_stats

    return {
        character_id: float(buffed_combat_stats(character, state, buffs).get("crit_damage", character.crit_damage))
        for character_id, character in characters.items()
    }
