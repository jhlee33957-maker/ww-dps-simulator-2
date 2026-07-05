from __future__ import annotations

from typing import Any

from simulator.buff_system import apply_buff, support_stat_context
from simulator.models import BuffData, CharacterData, CombatState


AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID = "aemeath_trailblazing_star_5set"
TRAILBLAZING_STAR_SET_KEY = "trailblazing_star"
MORNYE_SYNTONY_FIELD_OFF_TUNE_BUFF_ID = "mornye_syntony_field_off_tune_buildup_rate"
MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID = "mornye_halo_of_starry_radiance_5set"
HALO_OF_STARRY_RADIANCE_SET_KEY = "halo_of_starry_radiance"
TEAM_HEAL_EVENT_TAG = "team_heal"


def active_echo_sets_for_characters(characters: dict[str, CharacterData]) -> dict[str, dict[str, Any]]:
    return {
        character_id: dict(character.echo_sets)
        for character_id, character in characters.items()
        if character.echo_sets
    }


def trailblazing_star_config(character: CharacterData | None) -> dict[str, Any]:
    if character is None:
        return {}
    config = (character.echo_sets or {}).get(TRAILBLAZING_STAR_SET_KEY) or {}
    return dict(config) if isinstance(config, dict) else {}


def trailblazing_star_enabled(character: CharacterData | None) -> bool:
    config = trailblazing_star_config(character)
    return int(config.get("pieces") or 0) >= 5 and bool(config.get("conditional_5set_enabled"))


def halo_of_starry_radiance_config(character: CharacterData | None) -> dict[str, Any]:
    if character is None:
        return {}
    config = (character.echo_sets or {}).get(HALO_OF_STARRY_RADIANCE_SET_KEY) or {}
    return dict(config) if isinstance(config, dict) else {}


def halo_of_starry_radiance_enabled(character: CharacterData | None) -> bool:
    config = halo_of_starry_radiance_config(character)
    return int(config.get("pieces") or 0) >= 5 and bool(config.get("conditional_5set_enabled"))


def halo_of_starry_radiance_atk_percent(current_off_tune_buildup_rate: float) -> float:
    return min(max(0.0, float(current_off_tune_buildup_rate)) * 0.20, 0.25)


def echo_set_base_log_fields() -> dict[str, Any]:
    return {
        "echo_set_triggered_buff_ids": [],
        "echo_set_buff_refreshed": False,
        "aemeath_trailblazing_star_5set_applied_before_triggering_damage": False,
        "trailblazing_star_5set_same_action_application": False,
        "trailblazing_star_5set_application_timing": None,
        "team_heal_event_triggered": False,
        "halo_of_starry_radiance_5set_unavailable_reason": None,
    }


def merge_echo_set_logs(*logs: dict[str, Any]) -> dict[str, Any]:
    merged = echo_set_base_log_fields()
    for log in logs:
        if not log:
            continue
        ids = [
            buff_id
            for buff_id in [
                *merged.get("echo_set_triggered_buff_ids", []),
                *log.get("echo_set_triggered_buff_ids", []),
            ]
            if buff_id
        ]
        merged.update(log)
        merged["echo_set_triggered_buff_ids"] = list(dict.fromkeys(ids))
        merged["echo_set_buff_refreshed"] = bool(
            merged.get("echo_set_buff_refreshed", False) or log.get("echo_set_buff_refreshed", False)
        )
        merged["team_heal_event_triggered"] = bool(
            merged.get("team_heal_event_triggered", False) or log.get("team_heal_event_triggered", False)
        )
    return merged


def apply_echo_set_event_buffs(
    *,
    actor_character_id: str | None,
    emitted_event_tags: list[str],
    characters: dict[str, CharacterData],
    state: CombatState,
    buffs: dict[str, BuffData],
    application_time: float,
    applied_before_triggering_damage: bool = False,
) -> dict[str, Any]:
    log = echo_set_base_log_fields()
    if not actor_character_id or not emitted_event_tags:
        return log

    character = characters.get(actor_character_id)
    config = trailblazing_star_config(character)
    if not trailblazing_star_enabled(character):
        return log

    trigger_tags = {str(tag) for tag in config.get("trigger_event_tags", [])}
    if not trigger_tags.intersection(emitted_event_tags):
        return log

    buff_id = str(config.get("buff_id") or AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID)
    buff = buffs.get(buff_id)
    if buff is None:
        return log

    was_active = _active_buff_exists(state, buff_id)
    apply_buff(state, buff, actor_character_id)
    state.echo_set_trigger_counts[buff_id] = state.echo_set_trigger_counts.get(buff_id, 0) + 1
    _record_echo_set_window(state, buff_id, actor_character_id, application_time, float(buff.duration))

    log["echo_set_triggered_buff_ids"] = [buff_id]
    log["echo_set_buff_refreshed"] = was_active
    log["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] = bool(applied_before_triggering_damage)
    log["trailblazing_star_5set_same_action_application"] = bool(applied_before_triggering_damage)
    if applied_before_triggering_damage:
        log["trailblazing_star_5set_application_timing"] = "same_action_aggregate_approximation"
    return log


def apply_syntony_field_off_tune_buff(
    *,
    state: CombatState,
    source_character_id: str = "mornye",
    duration: float = 25.0,
    constellation: int = 0,
    application_time: float = 0.0,
) -> dict[str, Any]:
    c2_active = int(constellation or 0) >= 2
    value = 0.5 + (0.2 if c2_active else 0.0)
    buff = BuffData(
        id=MORNYE_SYNTONY_FIELD_OFF_TUNE_BUFF_ID,
        name="Mornye Syntony Field Off-Tune Buildup Rate",
        duration=float(duration),
        modifier_type="boost",
        value=0.0,
        target="team",
        target_scope="team",
        source_character_id=source_character_id,
        max_stacks=1,
        stacking_rule="refresh_duration",
        support_stat_modifiers={"off_tune_buildup_rate_add": value},
        metadata={
            "source_character_id": source_character_id,
            "source_status": "workbook_confirmed",
            "source": "角色-女!D4122",
            "dynamic_support_value": value,
            "c2_off_tune_bonus_active": c2_active,
            "mornye_constellation": int(constellation or 0),
        },
    )
    was_active = _active_buff_exists(state, buff.id)
    apply_buff(state, buff, source_character_id)
    return {
        "syntony_field_off_tune_bonus_active": True,
        "syntony_field_off_tune_bonus_value": value,
        "c2_off_tune_bonus_active": c2_active,
        "mornye_constellation": int(constellation or 0),
        "syntony_field_off_tune_buff_refreshed": was_active,
        "syntony_field_off_tune_buff_duration": float(duration),
        "syntony_field_off_tune_bonus_source": "角色-女!D4122",
        "syntony_field_off_tune_bonus_application_time": application_time,
    }


def apply_mornye_halo_of_starry_radiance_5set_event_buff(
    *,
    source_character_id: str | None,
    emitted_event_tags: list[str],
    characters: dict[str, CharacterData],
    state: CombatState,
    buffs: dict[str, BuffData],
    application_time: float,
    event_source: str,
) -> dict[str, Any]:
    log = echo_set_base_log_fields()
    if source_character_id != "mornye" or TEAM_HEAL_EVENT_TAG not in set(emitted_event_tags):
        log["halo_of_starry_radiance_5set_unavailable_reason"] = "no_mornye_team_heal_event"
        return log
    character = characters.get("mornye")
    config = halo_of_starry_radiance_config(character)
    if not halo_of_starry_radiance_enabled(character):
        log["team_heal_event_triggered"] = True
        log["halo_of_starry_radiance_5set_unavailable_reason"] = "mornye_halo_5set_not_enabled"
        _record_team_heal_event(state, source_character_id, application_time, event_source, applied_buff_id=None)
        return log

    trigger_tags = {str(tag) for tag in config.get("trigger_event_tags", [])}
    if TEAM_HEAL_EVENT_TAG not in trigger_tags:
        log["team_heal_event_triggered"] = True
        log["halo_of_starry_radiance_5set_unavailable_reason"] = "halo_profile_missing_team_heal_trigger"
        _record_team_heal_event(state, source_character_id, application_time, event_source, applied_buff_id=None)
        return log

    buff_id = str(config.get("buff_id") or MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID)
    buff = buffs.get(buff_id)
    if buff is None:
        log["team_heal_event_triggered"] = True
        log["halo_of_starry_radiance_5set_unavailable_reason"] = "halo_buff_data_missing"
        _record_team_heal_event(state, source_character_id, application_time, event_source, applied_buff_id=None)
        return log

    context = support_stat_context(character, state, buffs)
    current_off_tune = float(context["current_off_tune_buildup_rate"])
    value = halo_of_starry_radiance_atk_percent(current_off_tune)
    runtime_buff = buff.model_copy(deep=True)
    runtime_buff.value = value
    runtime_buff.metadata = {
        **runtime_buff.metadata,
        "dynamic_value": value,
        "current_off_tune_buildup_rate": current_off_tune,
        "base_off_tune_buildup_rate": context["base_off_tune_buildup_rate"],
        "runtime_off_tune_buildup_rate_bonus": context["runtime_off_tune_buildup_rate_bonus"],
        "event_source": event_source,
    }

    was_active = _active_buff_exists(state, buff_id)
    apply_buff(state, runtime_buff, source_character_id)
    state.echo_set_trigger_counts[buff_id] = state.echo_set_trigger_counts.get(buff_id, 0) + 1
    _record_echo_set_window(state, buff_id, source_character_id, application_time, float(runtime_buff.duration))
    _record_team_heal_event(state, source_character_id, application_time, event_source, applied_buff_id=buff_id)

    log.update(
        {
            "echo_set_triggered_buff_ids": [buff_id],
            "echo_set_buff_refreshed": was_active,
            "team_heal_event_triggered": True,
            "halo_of_starry_radiance_5set_unavailable_reason": None,
        }
    )
    return log


def echo_set_active_buff_ids(state: CombatState, buffs: dict[str, BuffData]) -> list[str]:
    active_ids: list[str] = []
    for active in state.active_buffs:
        if active.remaining_duration <= 0.0:
            continue
        buff = buffs.get(active.buff_id)
        if buff is not None and buff.metadata.get("source_type") == "echo_set":
            active_ids.append(active.buff_id)
    return active_ids


def trailblazing_star_uptime_seconds(state: CombatState, combat_time: float | None = None) -> float:
    return echo_set_buff_uptime_seconds(state, AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID, combat_time)


def halo_of_starry_radiance_uptime_seconds(state: CombatState, combat_time: float | None = None) -> float:
    return echo_set_buff_uptime_seconds(state, MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID, combat_time)


def echo_set_buff_uptime_seconds(state: CombatState, buff_id: str, combat_time: float | None = None) -> float:
    total = 0.0
    limit = combat_time if combat_time is not None else None
    for window in state.echo_set_buff_windows:
        if window.get("buff_id") != buff_id:
            continue
        start = float(window.get("start_time", 0.0))
        end = float(window.get("end_time", start))
        if limit is not None:
            end = min(end, float(limit))
        total += max(0.0, end - start)
    return total


def _active_buff_exists(state: CombatState, buff_id: str) -> bool:
    return any(active.buff_id == buff_id and active.remaining_duration > 0.0 for active in state.active_buffs)


def _record_echo_set_window(
    state: CombatState,
    buff_id: str,
    character_id: str | None,
    application_time: float,
    duration: float,
) -> None:
    window_end_time = application_time + duration
    for window in reversed(state.echo_set_buff_windows):
        if window.get("buff_id") == buff_id and window.get("character_id") == character_id:
            if float(window.get("end_time", 0.0)) >= application_time - 1e-9:
                window["end_time"] = window_end_time
                window["duration"] = max(0.0, window_end_time - float(window.get("start_time", application_time)))
                return
    state.echo_set_buff_windows.append(
        {
            "buff_id": buff_id,
            "character_id": character_id,
            "start_time": application_time,
            "end_time": window_end_time,
            "duration": duration,
        }
    )


def _record_team_heal_event(
    state: CombatState,
    source_character_id: str,
    application_time: float,
    event_source: str,
    *,
    applied_buff_id: str | None,
) -> None:
    state.mechanic_event_emitted_counts[TEAM_HEAL_EVENT_TAG] = (
        state.mechanic_event_emitted_counts.get(TEAM_HEAL_EVENT_TAG, 0) + 1
    )
    state.mechanic_event_log.append(
        {
            "event_tag": TEAM_HEAL_EVENT_TAG,
            "trigger_id": "mornye_syntony_field_heal_proxy",
            "character_id": source_character_id,
            "source_status": "simplified_field_uptime_heal_proxy",
            "combat_time": application_time,
            "damage_added": 0.0,
            "event_source": event_source,
            "applied_buff_id": applied_buff_id,
        }
    )
