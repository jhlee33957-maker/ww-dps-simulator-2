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
    "stardust_resonance_extra_effects",
    "aemeath_s1_kill_trajectory_transfer",
    "aemeath_s2_kill_triggered_detonation",
    "aemeath_s5_all_effects",
    "enemy_movement_or_pull",
    "player_survival_effects",
    "multi_target_trajectory_tracking",
]
AEMEATH_S3_HEAVY_MODE_ACTION_IDS = {
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_2",
}
AEMEATH_SYNC_STRIKE_ACTION_IDS = {
    "aemeath_sync_strike_armament_merge",
    "aemeath_sync_strike_call_of_dawn",
}
# 角色-女!D2844 gives Fusion Trajectory a 30-second duration, but specifies no timed
# lifetime for Fusion Effect itself. It remains present while the target is in combat.
FUSION_EFFECT_DURATION_SECONDS: float | None = None
FUSION_TRAIL_DURATION_SECONDS = 30.0
FUSION_APPLICATION_COOLDOWN_SECONDS = 3.0


def aemeath_resonance_mode_from_config(config: dict[str, Any] | None) -> str:
    aemeath_config = ((config or {}).get("aemeath") or {})
    mode = str(aemeath_config.get("aemeath_resonance_mode", "unresolved"))
    return mode if mode in SUPPORTED_AEMEATH_RESONANCE_MODES else "unresolved"


def apply_aemeath_fusion_effect_event(
    state: CombatState,
    *,
    source_character_id: str,
    source_action_id: str,
    source_event_id: str,
    apply_base_effect: bool,
    counts_as_party_application: bool,
    combat_time: float,
    cooldown_seconds: float = FUSION_APPLICATION_COOLDOWN_SECONDS,
    cooldown_source_ref: str = "\u89d2\u8272-\u5973!D2844",
) -> dict[str, Any]:
    """Apply one source-qualified Fusion event to Aemeath's authoritative target state."""
    data = state.character_mechanics_state.setdefault("aemeath", {})
    account = state.character_mechanics_state.get("_account_constellation", {})
    if aemeath_resonance_mode_from_config(state.mechanics_config) != "fusion_burst":
        return {"applied": False, "reason": "mode_not_fusion_burst"}
    cooldowns = data.setdefault("fusion_application_last_trigger_time", {})
    cooldown_key = f"{source_character_id}:{source_event_id}"
    last_trigger = cooldowns.get(cooldown_key)
    now = float(combat_time)
    if cooldown_seconds > 0.0 and last_trigger is not None and now - float(last_trigger) < cooldown_seconds:
        return {
            "applied": False,
            "reason": "source_cooldown",
            "cooldown_key": cooldown_key,
            "remaining_seconds": cooldown_seconds - (now - float(last_trigger)),
        }
    if apply_base_effect:
        effect_before = int(data.get("fusion_effect_stacks", 0) or 0)
        effect_after = min(int(data.get("fusion_effect_max_stacks", 10) or 10), effect_before + 1)
        data["fusion_effect_stacks"] = effect_after
        data["fusion_effect_remaining"] = 0.0
    else:
        effect_before = int(data.get("fusion_effect_stacks", 0) or 0)
        effect_after = effect_before
    trail_before = int(data.get("fusion_trail_stacks", 0) or 0)
    base_gain = 1 if counts_as_party_application else 0
    s6_gain = 1 if counts_as_party_application and int(account.get("aemeath_sequence", 0) or 0) >= 6 else 0
    cap = 60 if int(account.get("aemeath_sequence", 0) or 0) >= 6 else 30
    trail_after = min(cap, trail_before + base_gain + s6_gain)
    if counts_as_party_application:
        data["fusion_trail_stacks"] = trail_after
        data["fusion_trail_remaining"] = FUSION_TRAIL_DURATION_SECONDS
    if cooldown_seconds > 0.0:
        cooldowns[cooldown_key] = now
    event = {
        "event_type": "fusion_effect_application",
        "source_character_id": source_character_id,
        "source_action_id": source_action_id,
        "source_event_id": source_event_id,
        "cooldown_key": cooldown_key,
        "cooldown_seconds": cooldown_seconds,
        "cooldown_source_ref": cooldown_source_ref,
        "fusion_effect_stacks_before": effect_before,
        "fusion_effect_stacks_after": effect_after,
        "base_trajectory_gain": base_gain,
        "s6_post_application_gain": s6_gain,
        "fusion_trajectory_stacks_before": trail_before,
        "fusion_trajectory_stacks_after": trail_after,
        "fusion_effect_duration_seconds": FUSION_EFFECT_DURATION_SECONDS,
        "fusion_effect_duration_policy": "persistent_while_in_combat_source_duration_not_specified",
        "fusion_trajectory_remaining": FUSION_TRAIL_DURATION_SECONDS if counts_as_party_application else 0.0,
        "source_ref": cooldown_source_ref,
    }
    data.setdefault("fusion_trail_event_log", []).append(event)
    return {"applied": True, **event}


def mechanic_event_metadata_for_config(config: dict[str, Any] | None) -> dict[str, Any]:
    mode = aemeath_resonance_mode_from_config(config)
    aemeath_config = ((config or {}).get("aemeath") or {})
    unresolved_reason = None
    if mode == "unresolved":
        unresolved_reason = "aemeath_resonance_mode_unresolved_no_events_emit"
    return {
        "aemeath_resonance_mode": mode,
        "aemeath_resonance_mode_source": aemeath_config.get("aemeath_resonance_mode_source", "default"),
        "aemeath_resonance_mode_evidence_source": AEMEATH_RESONANCE_MODE_SOURCE,
        "mechanic_event_trigger_action_ids": list(AEMEATH_RESONANCE_MODE_TRIGGER_ACTION_IDS),
        "mechanic_event_transition_trigger_action_ids": list(AEMEATH_RESONANCE_MODE_TRANSITION_TRIGGER_ACTION_IDS),
        "mechanic_event_unresolved_reason": unresolved_reason,
        "unsupported_aemeath_followup_mechanics": list(UNSUPPORTED_AEMEATH_FOLLOWUP_MECHANICS),
    }


def preview_mechanic_event_trigger(
    action: ActionData,
    state: CombatState,
    *,
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
    if action.mechanic_event_tags:
        log["emitted_mechanic_event_tags"] = list(dict.fromkeys(action.mechanic_event_tags))
        log["mechanic_event_triggered"] = True
        log["mechanic_event_trigger_id"] = "declared_mechanic_event_tags"
        log["mechanic_event_source_status"] = action.data_status
        return log
    if (
        action.id in AEMEATH_S3_HEAVY_MODE_ACTION_IDS
        and bool(state.character_mechanics_state.get("aemeath", {}).get("instant_response", False))
        and int(
        state.character_mechanics_state.get("_account_constellation", {}).get("aemeath_sequence", 0) or 0
        ) >= 3
    ):
        mode = aemeath_resonance_mode_from_config(state.mechanics_config)
        event_tag = {"tune_rupture": "tune_rupture_shifting", "fusion_burst": "fusion_burst"}.get(mode)
        if event_tag:
            log.update(
                {
                    "emitted_mechanic_event_tags": [event_tag],
                    "mechanic_event_triggered": True,
                    "mechanic_event_trigger_id": "aemeath_s3_enhanced_heavy_mode_effect",
                    "aemeath_resonance_mode": mode,
                    "mechanic_event_source_status": "workbook_confirmed",
                }
            )
        return log
    if not action.mechanic_event_triggers:
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

        log["emitted_mechanic_event_tags"] = [event_tag]
        log["mechanic_event_triggered"] = True
        return log

    return log


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
    if direct_damage <= 0.0:
        return log

    if (
        action.id in AEMEATH_S3_HEAVY_MODE_ACTION_IDS
        and bool(state.character_mechanics_state.get("aemeath", {}).get("instant_response", False))
        and int(
        state.character_mechanics_state.get("_account_constellation", {}).get("aemeath_sequence", 0) or 0
        ) >= 3
    ):
        mode = aemeath_resonance_mode_from_config(state.mechanics_config)
        event_tag = {"tune_rupture": "tune_rupture_shifting", "fusion_burst": "fusion_burst"}.get(mode)
        if event_tag:
            if event_tag == "tune_rupture_shifting":
                state.target_tune_shift_state = "tune_rupture_shifting"
                state.target_tune_shift_remaining = 8.0
            elif event_tag == "fusion_burst":
                application = apply_aemeath_fusion_effect_event(
                    state,
                    source_character_id=action.character_id,
                    source_action_id=action.id,
                    source_event_id="aemeath_s3_enhanced_heavy_mode_effect",
                    apply_base_effect=True,
                    counts_as_party_application=True,
                    combat_time=action_start_combat_time,
                    cooldown_seconds=0.0,
                    cooldown_source_ref="base!FG73 / base!FP73",
                )
                log["fusion_application"] = application
                if not application["applied"]:
                    log["mechanic_event_cooldown_blocked"] = application.get("reason") == "source_cooldown"
            state.mechanic_event_emitted_counts[event_tag] = state.mechanic_event_emitted_counts.get(event_tag, 0) + 1
            state.mechanic_event_log.append(
                {
                    "event_tag": event_tag,
                    "trigger_id": "aemeath_s3_enhanced_heavy_mode_effect",
                    "action_id": action.id,
                    "character_id": action.character_id,
                    "aemeath_resonance_mode": mode,
                    "source_status": "workbook_confirmed",
                    "combat_time": action_start_combat_time,
                    "damage_added": 0.0,
                }
            )
            log.update(
                {
                    "emitted_mechanic_event_tags": [event_tag],
                    "mechanic_event_triggered": True,
                    "mechanic_event_trigger_id": "aemeath_s3_enhanced_heavy_mode_effect",
                    "aemeath_resonance_mode": mode,
                    "mechanic_event_source_status": "workbook_confirmed",
                }
            )
        return log

    if action.mechanic_event_tags:
        event_tags = list(dict.fromkeys(action.mechanic_event_tags))
        for event_tag in event_tags:
            state.mechanic_event_emitted_counts[event_tag] = state.mechanic_event_emitted_counts.get(event_tag, 0) + 1
            state.mechanic_event_log.append(
                {
                    "event_tag": event_tag,
                    "trigger_id": "declared_mechanic_event_tags",
                    "action_id": action.id,
                    "character_id": action.character_id,
                    "source_status": action.data_status,
                    "combat_time": action_start_combat_time,
                    "damage_added": 0.0,
                }
            )
        log["emitted_mechanic_event_tags"] = event_tags
        log["mechanic_event_triggered"] = True
        log["mechanic_event_trigger_id"] = "declared_mechanic_event_tags"
        log["mechanic_event_source_status"] = action.data_status
        return log

    if not action.mechanic_event_triggers:
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
        if event_tag == "tune_rupture_shifting":
            state.target_tune_shift_state = "tune_rupture_shifting"
            state.target_tune_shift_remaining = 8.0
            event_record["target_tune_shift_state"] = state.target_tune_shift_state
            event_record["target_tune_shift_duration_source_status"] = "user_supplied_skill_screenshot_not_embedded"
        elif event_tag == "fusion_burst":
            if action.id in AEMEATH_SYNC_STRIKE_ACTION_IDS:
                event_record["fusion_application_timing"] = "post_settlement_after_action"
            else:
                application = apply_aemeath_fusion_effect_event(
                    state,
                    source_character_id=action.character_id,
                    source_action_id=action.id,
                    source_event_id=action.id,
                    apply_base_effect=True,
                    counts_as_party_application=True,
                    combat_time=action_start_combat_time,
                )
                event_record["fusion_application"] = application
                if not application["applied"]:
                    log["mechanic_event_cooldown_blocked"] = application.get("reason") == "source_cooldown"
        state.mechanic_event_log.append(event_record)
        log["emitted_mechanic_event_tags"] = [event_tag]
        log["mechanic_event_triggered"] = True
        return log

    return log
