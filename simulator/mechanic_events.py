from __future__ import annotations

from typing import Any

from simulator.models import ActionData, CombatState


AEMEATH_RESONANCE_MODE_TRIGGER_ID = "aemeath_resonance_mode_damage_trigger"
AEMEATH_RESONANCE_MODE_SOURCE_STATUS = "user_supplied_skill_screenshot_not_embedded"
AEMEATH_RESONANCE_MODE_SOURCE = "user_supplied_skill_screenshot"
SUPPORTED_AEMEATH_RESONANCE_MODES = {"fusion_burst", "tune_rupture", "unresolved"}
AEMEATH_RESONANCE_MODE_TRIGGER_ACTION_IDS = [
    "aemeath_basic_form_stage_3",
    "aemeath_basic_form_stage_4",
    "aemeath_mech_basic_stage_3",
    "aemeath_mech_basic_stage_4",
    "aemeath_sync_strike_armament_merge",
    "aemeath_sync_strike_call_of_dawn",
]
AEMEATH_RESONANCE_MODE_TRANSITION_TRIGGER_ACTION_IDS = [
    "aemeath_qte_intro_human",
    "aemeath_qte_intro_mech",
]
UNSUPPORTED_AEMEATH_FOLLOWUP_MECHANICS = [
    "fusion_burst_explosion_damage",
    "fusion_trail",
    "rupturous_trail",
    "seraphic_duet_extra_tune_rupture_damage",
    "seraphic_duet_fusion_burst_multiplier",
    "stardust_resonance_extra_effects",
]


def aemeath_resonance_mode_from_config(config: dict[str, Any] | None) -> str:
    aemeath_config = ((config or {}).get("aemeath") or {})
    mode = str(aemeath_config.get("aemeath_resonance_mode", "unresolved"))
    return mode if mode in SUPPORTED_AEMEATH_RESONANCE_MODES else "unresolved"


def mechanic_event_metadata_for_config(config: dict[str, Any] | None) -> dict[str, Any]:
    mode = aemeath_resonance_mode_from_config(config)
    unresolved_reason = None
    if mode == "unresolved":
        unresolved_reason = "aemeath_resonance_mode_unresolved_no_events_emit"
    return {
        "aemeath_resonance_mode": mode,
        "aemeath_resonance_mode_source": AEMEATH_RESONANCE_MODE_SOURCE,
        "mechanic_event_trigger_action_ids": list(AEMEATH_RESONANCE_MODE_TRIGGER_ACTION_IDS),
        "mechanic_event_transition_trigger_action_ids": list(AEMEATH_RESONANCE_MODE_TRANSITION_TRIGGER_ACTION_IDS),
        "mechanic_event_unresolved_reason": unresolved_reason,
        "unsupported_aemeath_followup_mechanics": list(UNSUPPORTED_AEMEATH_FOLLOWUP_MECHANICS),
    }


def process_mechanic_event_triggers(
    action: ActionData,
    state: CombatState,
    *,
    direct_damage: float,
    action_start_combat_time: float,
) -> dict[str, Any]:
    log = {
        "emitted_mechanic_event_tags": [],
        "mechanic_event_triggered": False,
        "mechanic_event_trigger_id": None,
        "mechanic_event_cooldown_blocked": False,
        "aemeath_resonance_mode": None,
        "mechanic_event_source_status": None,
        "mechanic_event_unresolved_reason": None,
    }
    if direct_damage <= 0.0 or not action.mechanic_event_triggers:
        return log

    for trigger in action.mechanic_event_triggers:
        if trigger.get("trigger_id") != AEMEATH_RESONANCE_MODE_TRIGGER_ID:
            continue
        log["mechanic_event_trigger_id"] = AEMEATH_RESONANCE_MODE_TRIGGER_ID
        log["mechanic_event_source_status"] = trigger.get("source_status")
        mode = aemeath_resonance_mode_from_config(state.mechanics_config)
        log["aemeath_resonance_mode"] = mode
        event_by_mode = trigger.get("event_by_aemeath_resonance_mode") or {}
        event_tag = event_by_mode.get(mode)
        if not event_tag:
            log["mechanic_event_unresolved_reason"] = "aemeath_resonance_mode_unresolved_no_events_emit"
            return log

        cooldown_seconds = float(trigger.get("cooldown_seconds", 0.0) or 0.0)
        cooldown_key = f"{action.character_id}:{action.id}:{AEMEATH_RESONANCE_MODE_TRIGGER_ID}"
        last_trigger_time = state.mechanic_event_last_trigger_time.get(cooldown_key)
        if last_trigger_time is not None and action_start_combat_time - last_trigger_time < cooldown_seconds:
            log["mechanic_event_cooldown_blocked"] = True
            return log

        state.mechanic_event_last_trigger_time[cooldown_key] = action_start_combat_time
        state.mechanic_event_emitted_counts[event_tag] = state.mechanic_event_emitted_counts.get(event_tag, 0) + 1
        event_record = {
            "event_tag": event_tag,
            "trigger_id": AEMEATH_RESONANCE_MODE_TRIGGER_ID,
            "action_id": action.id,
            "character_id": action.character_id,
            "aemeath_resonance_mode": mode,
            "source_status": trigger.get("source_status"),
            "combat_time": action_start_combat_time,
            "cooldown_seconds": cooldown_seconds,
            "damage_added": 0.0,
        }
        state.mechanic_event_log.append(event_record)
        log["emitted_mechanic_event_tags"] = [event_tag]
        log["mechanic_event_triggered"] = True
        return log

    return log
