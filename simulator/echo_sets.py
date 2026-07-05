from __future__ import annotations

from typing import Any

from simulator.buff_system import apply_buff
from simulator.models import BuffData, CharacterData, CombatState


AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID = "aemeath_trailblazing_star_5set"
TRAILBLAZING_STAR_SET_KEY = "trailblazing_star"


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
    log = {
        "echo_set_triggered_buff_ids": [],
        "echo_set_buff_refreshed": False,
        "aemeath_trailblazing_star_5set_applied_before_triggering_damage": False,
        "trailblazing_star_5set_same_action_application": False,
        "trailblazing_star_5set_application_timing": None,
    }
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

    was_active = any(active.buff_id == buff_id and active.remaining_duration > 0.0 for active in state.active_buffs)
    apply_buff(state, buff, actor_character_id)
    state.echo_set_trigger_counts[buff_id] = state.echo_set_trigger_counts.get(buff_id, 0) + 1

    window_end_time = application_time + float(buff.duration)
    if was_active:
        for window in reversed(state.echo_set_buff_windows):
            if window.get("buff_id") == buff_id and window.get("character_id") == actor_character_id:
                if float(window.get("end_time", 0.0)) >= application_time - 1e-9:
                    window["end_time"] = window_end_time
                    window["duration"] = max(0.0, window_end_time - float(window.get("start_time", application_time)))
                    break
        else:
            state.echo_set_buff_windows.append(
                {
                    "buff_id": buff_id,
                    "character_id": actor_character_id,
                    "start_time": application_time,
                    "end_time": window_end_time,
                    "duration": float(buff.duration),
                }
            )
    else:
        state.echo_set_buff_windows.append(
            {
                "buff_id": buff_id,
                "character_id": actor_character_id,
                "start_time": application_time,
                "end_time": window_end_time,
                "duration": float(buff.duration),
            }
        )

    log["echo_set_triggered_buff_ids"] = [buff_id]
    log["echo_set_buff_refreshed"] = was_active
    log["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] = bool(applied_before_triggering_damage)
    log["trailblazing_star_5set_same_action_application"] = bool(applied_before_triggering_damage)
    if applied_before_triggering_damage:
        log["trailblazing_star_5set_application_timing"] = "same_action_aggregate_approximation"
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
    total = 0.0
    limit = combat_time if combat_time is not None else None
    for window in state.echo_set_buff_windows:
        if window.get("buff_id") != AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID:
            continue
        start = float(window.get("start_time", 0.0))
        end = float(window.get("end_time", start))
        if limit is not None:
            end = min(end, float(limit))
        total += max(0.0, end - start)
    return total
