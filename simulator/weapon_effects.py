from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simulator.buff_system import apply_buff
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
    "crit_hit",
    "swap_in",
    "swap_out",
}
SUPPORTED_EFFECT_TYPES = {
    "resource_restore",
    "stat_buff",
    "party_stat_buff",
    "damage_bonus_buff",
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
