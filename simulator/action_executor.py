from __future__ import annotations

from typing import Any

from simulator.action_start_snapshot import ActionStartEffectSnapshot, capture_action_start_effect_snapshot
from simulator.anomaly_system import advance_anomalies, apply_anomaly
from simulator.buff_system import (
    apply_buff,
    apply_buff_modifiers_to_damage_context,
    _recalculate_attack_stats,
    buffed_combat_stats,
    damage_amp_for_action,
    has_required_buffs,
    tick_buffs,
)
from simulator.build_profiles import (
    action_damage_element,
    damage_bonus_breakdown,
    scaling_value_for_action,
    stat_component_log_fields,
    support_stat_log_fields,
)
from simulator.damage_formula import calc_def_multiplier, calc_res_multiplier, calculate_normal_damage
from simulator.echo_sets import (
    AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID,
    MORNYE_HIGH_SYNTONY_FIELD_DEF_BUFF_ID,
    MORNYE_HIGH_SYNTONY_FIELD_OFF_TUNE_BUFF_ID,
    MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID,
    apply_echo_set_event_buffs,
    echo_set_base_log_fields,
    merge_echo_set_logs,
)
from simulator.generated_damage import calculate_generated_damage_packet
from simulator.lynae_tune_strain import apply_lynae_tune_strain_damage_amp
from simulator.mechanic_events import preview_mechanic_event_trigger, process_mechanic_event_triggers
from simulator.models import ActionData, ActionResult, BuffData, CharacterData, CombatState, HitData, ScheduledEffectState, TimelineEntry
from simulator.resource_system import apply_resource_changes, can_pay_resources
from simulator.tune_break import (
    INTERFERED_MARKER_AMP_SOURCE,
    INTERFERED_MARKER_AMP_SOURCE_REF,
    INTERFERED_MARKER_AMP_SOURCE_STATUS,
    calculate_tune_break_damage_detail,
    current_interfered_damage_taken_amp,
)
from simulator.weapon_effects import weapon_runtime_damage_effects


INTERFERED_MARKER_BUFF_ID = "mornye_interfered_marker_damage_amp"


def is_action_valid(action: ActionData, state: CombatState) -> tuple[bool, str | None]:
    if action.action_type == "wait":
        return True, None

    if action.action_type == "swap":
        if action.character_id == state.active_character_id:
            return False, "Target character is already active."
        return True, None

    if action.character_id != state.active_character_id:
        return False, "Character is not active."

    if state.cooldowns.get(cooldown_key(action), 0.0) > 0.0:
        return False, "Action is on cooldown."

    if not can_pay_resources(state, action):
        return False, "Not enough resonance energy."

    if not has_required_buffs(state, action.required_buffs):
        return False, "Required buff is missing."

    return True, None


def cooldown_key(action: ActionData) -> str:
    return action.cooldown_group or action.id


def _active_interfered_marker_buff_damage_amp(
    state: CombatState,
    buffs: dict[str, BuffData],
    *,
    time_offset: float,
    action_start_snapshot: ActionStartEffectSnapshot | None = None,
) -> float:
    for active in state.active_buffs:
        if active.buff_id != INTERFERED_MARKER_BUFF_ID:
            continue
        if (
            action_start_snapshot is not None
            and action_start_snapshot.buff_active(INTERFERED_MARKER_BUFF_ID)
        ):
            pass
        elif active.remaining_duration <= time_offset:
            continue
        buff = buffs.get(active.buff_id)
        if buff is None or buff.modifier_type != "damage_amp":
            continue
        return float(active.metadata.get("dynamic_value", buff.value) or 0.0)
    return 0.0


def reduce_cooldowns(state: CombatState, elapsed: float) -> None:
    for action_id, remaining in list(state.cooldowns.items()):
        updated = max(0.0, remaining - elapsed)
        if updated > 0.0:
            state.cooldowns[action_id] = updated
        else:
            del state.cooldowns[action_id]


def _runtime_value(runtime_context: Any | None, key: str, default: Any = None) -> Any:
    if isinstance(runtime_context, dict):
        return runtime_context.get(key, default)
    if runtime_context is not None:
        return getattr(runtime_context, key, default)
    return default


def _has_valid_target(runtime_context: Any | None) -> bool:
    if bool(_runtime_value(runtime_context, "no_target", False)):
        return False
    for key in ("has_valid_target", "target_valid", "valid_target"):
        value = _runtime_value(runtime_context, key, None)
        if value is not None:
            return bool(value)
    return True


def _timing_override_applies(override_key: str, runtime_context: Any | None) -> bool:
    if override_key == "instant_response":
        return bool(_runtime_value(runtime_context, "instant_response", False))
    if override_key == "form_mech":
        return _runtime_value(runtime_context, "form") == "mech"
    if override_key == "wide_field_observation":
        return _runtime_value(runtime_context, "mode") == "wide_field_observation"
    if override_key == "lumiflow_gt_119":
        return float(_runtime_value(runtime_context, "lumiflow", 0.0) or 0.0) > 119.0
    if override_key == "no_target":
        return not _has_valid_target(runtime_context)
    raise ValueError(f"Unknown timing override key {override_key!r}")


def resolve_action_runtime_timing(action: ActionData, runtime_context: Any | None = None) -> tuple[float, float, float]:
    duration = action.duration
    action_time = action.effective_action_time
    combat_time_cost = action.effective_combat_time_cost
    for override_key, override in (action.timing_overrides or {}).items():
        if not _timing_override_applies(override_key, runtime_context):
            continue
        duration = float(override.get("duration", duration))
        action_time = float(override.get("action_time", action_time))
        combat_time_cost = float(override.get("combat_time_cost", action_time))
    return duration, action_time, combat_time_cost


def resolve_action_timing(action: ActionData, actor_state: Any | None = None) -> tuple[float, float]:
    _duration, action_time, combat_time_cost = resolve_action_runtime_timing(action, actor_state)
    return action_time, combat_time_cost


def combat_time_cutoff(
    combat_start_time: float,
    combat_time_cost: float,
    combat_duration: float | None,
) -> tuple[float, float, bool]:
    if combat_duration is None:
        return combat_start_time + combat_time_cost, combat_time_cost, False

    remaining_combat_time = max(0.0, combat_duration - combat_start_time)
    effective_combat_time_cost = min(combat_time_cost, remaining_combat_time)
    combat_time_end = min(combat_start_time + combat_time_cost, combat_duration)
    truncated_by_combat_limit = combat_time_cost > effective_combat_time_cost
    return combat_time_end, effective_combat_time_cost, truncated_by_combat_limit


def _hit_combat_offset(
    hit: HitData,
    *,
    action_time: float,
    combat_time_cost: float,
    untimed_fallback: bool,
) -> float:
    if combat_time_cost <= 0.0:
        return 0.0
    if untimed_fallback:
        return combat_time_cost
    if abs(combat_time_cost - action_time) <= 1e-9:
        return hit.time
    if action_time <= 0.0:
        return combat_time_cost
    return min(combat_time_cost, hit.time / action_time * combat_time_cost)


def _resolved_action_hits(action: ActionData, *, action_time: float) -> list[HitData]:
    resolved_hits: list[HitData] = []
    for hit in action.effective_hits():
        if hit.hit_time_mode == "resolved_action_end":
            resolved_hits.append(hit.model_copy(update={"time": action_time}))
        else:
            resolved_hits.append(hit)
    return resolved_hits


def _calculate_hit_damage(
    hit: HitData,
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    temporary_stat_modifiers: dict[str, float] | None = None,
    force_active_buff_ids: set[str] | None = None,
    action_start_snapshot: ActionStartEffectSnapshot | None = None,
    weapon_definitions: dict[str, Any] | None = None,
) -> tuple[float, dict]:
    transition_damage_action = bool((action.mechanic_effects or {}).get("transition_action"))
    if action.character_id is None or (action.action_type == "swap" and not transition_damage_action):
        return 0.0, {}

    character = characters[action.character_id]
    stats = buffed_combat_stats(
        character,
        state,
        buffs,
        time_offset=hit.time,
        force_active_buff_ids=force_active_buff_ids,
    )
    for stat_name, stat_value in (temporary_stat_modifiers or {}).items():
        if stat_name == "atk_percent":
            stats["runtime_atk_percent_bonus"] += float(stat_value)
        elif stat_name == "flat_atk":
            stats["runtime_atk_flat_bonus"] += float(stat_value)
            stats["runtime_flat_atk_bonus"] += float(stat_value)
        elif stat_name == "def_percent":
            stats["runtime_def_percent_bonus"] += float(stat_value)
        elif stat_name == "flat_def":
            stats["runtime_def_flat_bonus"] += float(stat_value)
        elif stat_name == "hp_percent":
            stats["runtime_hp_percent_bonus"] += float(stat_value)
        elif stat_name == "flat_hp":
            stats["runtime_hp_flat_bonus"] += float(stat_value)
        elif stat_name in stats:
            stats[stat_name] += float(stat_value)
    _recalculate_attack_stats(stats)
    damage_amp = damage_amp_for_action(
        action.character_id,
        action,
        state,
        buffs,
        time_offset=hit.time,
        force_active_buff_ids=force_active_buff_ids,
    )
    target_damage_taken_amp = (
        action_start_snapshot.target_damage_taken_amp
        if action_start_snapshot is not None
        else current_interfered_damage_taken_amp(state)
    )
    if target_damage_taken_amp > 0.0:
        damage_amp -= _active_interfered_marker_buff_damage_amp(
            state,
            buffs,
            time_offset=hit.time,
            action_start_snapshot=action_start_snapshot,
        )
    target_damage_taken_multiplier = 1.0 + target_damage_taken_amp
    damage_element = action_damage_element(action, character)
    runtime_weapon_effects = weapon_runtime_damage_effects(
        character=character,
        action=action,
        state=state,
        buffs=buffs,
        weapon_definitions=weapon_definitions or {},
        damage_element=damage_element,
        damage_bonus_category=action.damage_bonus_category or action.action_type or "other",
        hit_damage_category=hit.damage_category,
        time_offset=hit.time,
        action_start_snapshot=action_start_snapshot,
    )
    runtime_element_bonuses = dict(stats.get("damage_bonus_by_element_buff") or {})
    for element, value in (runtime_weapon_effects.get("runtime_element_bonus_by_element") or {}).items():
        runtime_element_bonuses[element] = runtime_element_bonuses.get(element, 0.0) + float(value)

    damage_bonus_context = damage_bonus_breakdown(
        character,
        action,
        additive_buff_bonus=float(stats.get("damage_bonus_buff", 0.0)),
        additive_element_bonuses=runtime_element_bonuses,
        echo_set_element_bonuses=stats.get("echo_set_damage_bonus_by_element") or {},
    )
    runtime_weapon_effects = weapon_runtime_damage_effects(
        character=character,
        action=action,
        state=state,
        buffs=buffs,
        weapon_definitions=weapon_definitions or {},
        damage_element=str(damage_bonus_context.get("damage_element") or damage_element),
        damage_bonus_category=str(damage_bonus_context.get("damage_bonus_category") or "other"),
        hit_damage_category=hit.damage_category,
        time_offset=hit.time,
        action_start_snapshot=action_start_snapshot,
    )
    all_attribute_bonus = float(runtime_weapon_effects.get("runtime_all_attribute_damage_bonus", 0.0) or 0.0)
    element_damage_bonus_after_weapon = float(damage_bonus_context.get("element_dmg_bonus", 0.0) or 0.0)
    element_damage_bonus_before_weapon = element_damage_bonus_after_weapon - all_attribute_bonus
    havoc_def_reduction = (
        action_start_snapshot.havoc_bane_def_reduction
        if action_start_snapshot is not None
        else 0.0
    )
    final_def_reduction = state.def_reduction + havoc_def_reduction
    scaling_stat, scaling_value = scaling_value_for_action(stats, action, character)
    def_ignore_before_weapon = float(stats["def_ignore"])
    def_ignore_bonus = float(runtime_weapon_effects.get("everbright_polestar_def_ignore_bonus", 0.0) or 0.0)
    total_def_ignore = def_ignore_before_weapon + def_ignore_bonus
    fusion_res_ignore_bonus = float(
        runtime_weapon_effects.get("everbright_polestar_fusion_res_ignore_bonus", 0.0) or 0.0
    )
    effective_res_before_weapon = state.enemy_res - state.res_pen
    effective_res_after_weapon = effective_res_before_weapon - fusion_res_ignore_bonus
    def_multiplier_before_weapon = calc_def_multiplier(
        int(stats["attacker_level"]),
        state.enemy_level,
        def_ignore_before_weapon,
        final_def_reduction,
    )
    def_multiplier_after_weapon = calc_def_multiplier(
        int(stats["attacker_level"]),
        state.enemy_level,
        total_def_ignore,
        final_def_reduction,
    )
    res_multiplier_before_weapon = calc_res_multiplier(effective_res_before_weapon)
    res_multiplier_after_weapon = calc_res_multiplier(effective_res_after_weapon)

    damage = 0.0
    tune_break_detail: dict[str, Any] = {}
    if hit.damage_category == "normal" and hit.damage_multiplier > 0.0:
        damage = calculate_normal_damage(
            skill_multiplier=hit.damage_multiplier,
            character_base_atk=stats["character_base_atk"],
            weapon_base_atk=stats["weapon_base_atk"],
            atk_percent=stats["atk_percent"],
            flat_atk=stats["flat_atk"],
            effective_attack=stats["effective_attack"],
            scaling_value=scaling_value,
            dmg_bonus=float(damage_bonus_context["effective_damage_bonus"]),
            crit_rate=stats["crit_rate"],
            crit_damage=stats["crit_damage"],
            boost=stats["boost"],
            enemy_res=state.enemy_res,
            res_pen=state.res_pen,
            attacker_level=int(stats["attacker_level"]),
            enemy_level=state.enemy_level,
            def_ignore=stats["def_ignore"],
            def_reduction=final_def_reduction,
            dmg_taken=stats["dmg_taken"],
            final_dmg_bonus=stats["final_dmg_bonus"],
        )
    elif hit.damage_category == "tune_break" and hit.tune_break_multiplier > 0.0:
        tune_break_detail = calculate_tune_break_damage_detail(
            tune_break_multiplier=hit.tune_break_multiplier,
            additional_tune_break_boost=action.tune_break_boost_points / 100.0,
            tune_dmg_bonus=state.tune_dmg_bonus,
            enemy_res=state.enemy_res,
            res_pen=state.res_pen + fusion_res_ignore_bonus,
            attacker_level=int(stats["attacker_level"]),
            enemy_level=state.enemy_level,
            def_ignore=total_def_ignore,
            def_reduction=final_def_reduction,
            tune_break_damage_type="tune_break",
            tune_break_element=action.damage_element or "unresolved",
            hit_id=hit.name,
        )
        damage = float(tune_break_detail["tune_break_damage"])
        damage_bonus_context = {
            "damage_category": "tune_break",
            "damage_bonus_category": "tune_break",
            "damage_element": action.damage_element or "unresolved",
            "raw_skill_category": action.raw_skill_category,
            "raw_damage_type": action.raw_damage_type,
            "all_dmg_bonus": 0.0,
            "category_dmg_bonus": 0.0,
            "element_dmg_bonus": 0.0,
            "runtime_element_damage_bonus": 0.0,
            "echo_set_damage_bonus": 0.0,
        "effective_damage_bonus": 0.0,
        }
        scaling_stat = "none"
        scaling_value = 0.0
    if damage > 0.0 and damage_amp != 0.0:
        damage = apply_buff_modifiers_to_damage_context(damage, damage_amp)
        if hit.damage_category == "tune_break" and tune_break_detail:
            tune_break_detail["tune_break_damage_before_damage_taken_amp"] = tune_break_detail["tune_break_damage"]
            tune_break_detail["tune_break_damage"] = damage
    damage_before_target_amp = damage
    target_amp_applied_to_direct_damage = (
        damage > 0.0
        and target_damage_taken_amp > 0.0
        and hit.damage_category in {"normal", "tune_break"}
    )
    if target_amp_applied_to_direct_damage:
        damage *= target_damage_taken_multiplier
        if hit.damage_category == "tune_break" and tune_break_detail:
            tune_break_detail["tune_break_damage_before_target_amp"] = damage_before_target_amp
            tune_break_detail["tune_break_damage_after_target_amp"] = damage
            tune_break_detail["tune_break_damage"] = damage
    target_damage_taken_amp_bonus_damage = damage - damage_before_target_amp
    damage_before_lynae_tune_strain_amp = damage
    damage, lynae_tune_strain_log = apply_lynae_tune_strain_damage_amp(
        damage,
        source_character_id=action.character_id if hit.damage_category in {"normal", "tune_break"} else None,
        state=state,
        characters=characters,
        buffs=buffs,
        time_offset=hit.time,
        force_active_buff_ids=force_active_buff_ids,
    )
    lynae_tune_strain_bonus_damage = float(
        lynae_tune_strain_log.get("lynae_tune_strain_damage_amp_bonus_damage", 0.0) or 0.0
    )
    if lynae_tune_strain_bonus_damage > 0.0 and hit.damage_category == "tune_break" and tune_break_detail:
        tune_break_detail["tune_break_damage_before_lynae_tune_strain_amp"] = damage_before_lynae_tune_strain_amp
        tune_break_detail["tune_break_damage_after_lynae_tune_strain_amp"] = damage
        tune_break_detail["tune_break_damage"] = damage

    detail = {
        "hit_time": hit.time,
        "hit_damage_category": hit.damage_category,
        "damage_category": hit.damage_category,
        "damage": damage,
        "damage_multiplier": hit.damage_multiplier,
        "tune_break_multiplier": hit.tune_break_multiplier,
        **damage_bonus_context,
        "scaling_stat": scaling_stat,
        "scaling_value": scaling_value,
        "stat_component_source": character.build_profile_id,
        **stat_component_log_fields(stats),
        **support_stat_log_fields(stats),
        "profile_completeness_status": character.profile_completeness_status,
        "implementation_status": character.implementation_status,
        "applied_havoc_bane_def_reduction": havoc_def_reduction,
        "applied_buff_summary": stats.get("active_buff_summary", []),
        "active_buff_ids": stats.get("active_buff_summary", []),
        "aemeath_trailblazing_star_5set_active": (
            AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in stats.get("active_buff_summary", [])
        ),
        "high_syntony_field_def_bonus_active": bool(stats.get("high_syntony_field_def_bonus_active", False)),
        "high_syntony_field_def_percent_bonus": float(stats.get("high_syntony_field_def_percent_bonus", 0.0) or 0.0),
        "high_syntony_field_off_tune_inherited": bool(stats.get("high_syntony_field_off_tune_inherited", False)),
        "high_syntony_field_heal_proxy_active": bool(stats.get("high_syntony_field_heal_proxy_active", False)),
        "high_syntony_field_healing_multiplier_bonus": float(
            stats.get("high_syntony_field_healing_multiplier_bonus", 0.0) or 0.0
        ),
        "high_syntony_field_healing_multiplier_metadata_only": bool(
            stats.get("high_syntony_field_healing_multiplier_metadata_only", True)
        ),
        "critical_protocol_high_syntony_created_before_damage": False,
        "high_syntony_field_same_action_application": False,
        "high_syntony_field_application_timing": None,
        "halo_atk_buff_does_not_affect_mornye_def_damage": (
            action.character_id == "mornye" and scaling_stat == "def"
        ),
        "halo_of_starry_radiance_5set_active": bool(stats.get("halo_of_starry_radiance_5set_active", False)),
        "halo_of_starry_radiance_5set_atk_percent_bonus": float(
            stats.get("halo_of_starry_radiance_5set_atk_percent_bonus", 0.0) or 0.0
        ),
        "static_mist_incoming_atk_buff_active": bool(stats.get("static_mist_incoming_atk_buff_active", False)),
        "static_mist_incoming_atk_percent_bonus": float(
            stats.get("static_mist_incoming_atk_percent_bonus", 0.0) or 0.0
        ),
        "pact_neonlight_incoming_atk_buff_active": bool(stats.get("pact_neonlight_incoming_atk_buff_active", False)),
        "pact_neonlight_incoming_atk_percent_bonus": float(
            stats.get("pact_neonlight_incoming_atk_percent_bonus", 0.0) or 0.0
        ),
        "hyvatia_incoming_all_attribute_buff_active": bool(
            stats.get("hyvatia_incoming_all_attribute_buff_active", False)
        ),
        "hyvatia_incoming_all_attribute_damage_bonus": float(
            stats.get("hyvatia_incoming_all_attribute_damage_bonus", 0.0) or 0.0
        ),
        "halo_of_starry_radiance_5set_applied_before_field_creation_damage": False,
        "halo_of_starry_radiance_5set_same_action_application": False,
        "halo_of_starry_radiance_5set_application_timing": None,
        "aemeath_trailblazing_star_5set_applied_before_triggering_damage": False,
        "trailblazing_star_5set_same_action_application": False,
        "trailblazing_star_5set_application_timing": None,
        "crit_rate_before_buffs": float(stats.get("crit_rate_before_buffs", character.crit_rate)),
        "crit_rate_after_buffs": float(stats.get("crit_rate_after_buffs", stats.get("crit_rate", 0.0))),
        "crit_damage_before_buffs": float(stats.get("crit_damage_before_buffs", character.crit_damage)),
        "crit_damage_after_buffs": float(stats.get("crit_damage_after_buffs", stats.get("crit_damage", 0.0))),
        "runtime_crit_damage_bonus": float(stats.get("runtime_crit_damage_bonus", 0.0) or 0.0),
        "everbright_polestar_all_attribute_bonus_active": bool(
            runtime_weapon_effects.get("everbright_polestar_all_attribute_bonus_active", False)
        ),
        "everbright_polestar_all_attribute_damage_bonus": all_attribute_bonus,
        "runtime_all_attribute_damage_bonus": all_attribute_bonus,
        "element_damage_bonus_before_weapon": element_damage_bonus_before_weapon,
        "element_damage_bonus_after_weapon": element_damage_bonus_after_weapon,
        "everbright_polestar_liberation_penetration_active": bool(
            runtime_weapon_effects.get("everbright_polestar_liberation_penetration_active", False)
        ),
        "everbright_polestar_liberation_penetration_remaining": float(
            runtime_weapon_effects.get("everbright_polestar_liberation_penetration_remaining", 0.0) or 0.0
        ),
        "def_ignore_before_weapon": def_ignore_before_weapon,
        "everbright_polestar_def_ignore_bonus": def_ignore_bonus,
        "total_def_ignore": total_def_ignore,
        "def_multiplier_before_weapon": def_multiplier_before_weapon,
        "def_multiplier_after_weapon": def_multiplier_after_weapon,
        "enemy_res_before_weapon": effective_res_before_weapon,
        "everbright_polestar_fusion_res_ignore_bonus": fusion_res_ignore_bonus,
        "enemy_res_after_weapon": effective_res_after_weapon,
        "res_multiplier_before_weapon": res_multiplier_before_weapon,
        "res_multiplier_after_weapon": res_multiplier_after_weapon,
        "damage_element_fallback_used_for_weapon_res_ignore": (
            action.damage_element in (None, "", "generic", "unresolved")
            and character.element
            and str(damage_bonus_context.get("damage_element") or "") == str(character.element).lower()
        ),
        "weapon_effect_source_status": runtime_weapon_effects.get("weapon_effect_source_status"),
        "starfield_calibrator_party_crit_damage_active": bool(
            stats.get("starfield_calibrator_party_crit_damage_active", False)
        ),
        "starfield_calibrator_party_crit_damage_bonus": float(
            stats.get("starfield_calibrator_party_crit_damage_bonus", 0.0) or 0.0
        ),
        "applied_damage_amp": damage_amp,
        "target_damage_taken_amp": target_damage_taken_amp if target_amp_applied_to_direct_damage else 0.0,
        "target_damage_taken_multiplier": target_damage_taken_multiplier if target_amp_applied_to_direct_damage else 1.0,
        "target_damage_taken_amp_source": (
            INTERFERED_MARKER_AMP_SOURCE if target_amp_applied_to_direct_damage else None
        ),
        "target_damage_taken_amp_source_status": (
            INTERFERED_MARKER_AMP_SOURCE_STATUS if target_amp_applied_to_direct_damage else None
        ),
        "target_damage_taken_amp_source_ref": (
            INTERFERED_MARKER_AMP_SOURCE_REF if target_amp_applied_to_direct_damage else None
        ),
        "target_damage_taken_amp_bonus_damage": target_damage_taken_amp_bonus_damage,
        **lynae_tune_strain_log,
        "damage_before_lynae_tune_strain_amp": damage_before_lynae_tune_strain_amp,
        "damage_after_lynae_tune_strain_amp": damage,
        "normal_damage_before_target_amp": damage_before_target_amp if hit.damage_category == "normal" else 0.0,
        "normal_damage_after_target_amp": damage if hit.damage_category == "normal" else 0.0,
        "interfered_marker_amp_applied_to_direct_damage": (
            target_amp_applied_to_direct_damage and hit.damage_category == "normal"
        ),
        "tune_break_damage_receives_existing_interfered_marker_amp": (
            target_amp_applied_to_direct_damage and hit.damage_category == "tune_break"
        ),
        "tune_break_damage_receives_newly_applied_interfered_marker_amp": False,
        "tune_break_damage_before_target_amp": (
            damage_before_target_amp if hit.damage_category == "tune_break" else 0.0
        ),
        "tune_break_damage_after_target_amp": damage if hit.damage_category == "tune_break" else 0.0,
        "name": hit.name,
        **tune_break_detail,
    }
    return damage, detail


def _calculate_hit_damage_totals(
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    *,
    action_time: float,
    combat_time_cost: float,
    combat_start_time: float,
    combat_duration: float | None,
    truncated_by_combat_limit: bool,
    action_damage_multiplier: float = 1.0,
    temporary_stat_modifiers: dict[str, float] | None = None,
    force_active_buff_ids: set[str] | None = None,
    action_start_snapshot: ActionStartEffectSnapshot | None = None,
    weapon_definitions: dict[str, Any] | None = None,
) -> tuple[float, float, list[dict], dict[str, float], float, dict[str, Any], dict[str, Any]]:
    normal_damage = 0.0
    tune_break_damage = 0.0
    damage_after_cutoff_excluded = 0.0
    hit_details: list[dict] = []
    damage_by_category: dict[str, float] = {}
    action_damage_bonus_context: dict[str, Any] = {}
    direct_damage_taken_amp_total_bonus_damage = 0.0
    lynae_tune_strain_damage_amp_bonus_damage = 0.0
    lynae_tune_strain_damage_amp = 0.0
    lynae_tune_strain_damage_multiplier = 1.0
    lynae_tune_strain_source_status: str | None = None
    lynae_tune_strain_source_ref: str | None = None
    interfered_marker_direct_damage_amp_applied_count = 0
    tune_break_damage_receives_existing_interfered_marker_amp = False
    tune_break_damage_receives_newly_applied_interfered_marker_amp = False
    tune_break_damage_before_target_amp = 0.0
    tune_break_damage_after_target_amp = 0.0
    has_explicit_hit_timing = bool(action.hits)

    for hit in sorted(_resolved_action_hits(action, action_time=action_time), key=lambda item: item.time):
        if hit.time > action_time:
            continue
        damage, detail = _calculate_hit_damage(
            hit,
            action,
            state,
            characters,
            buffs,
            temporary_stat_modifiers,
            force_active_buff_ids=force_active_buff_ids,
            action_start_snapshot=action_start_snapshot,
            weapon_definitions=weapon_definitions,
        )
        if damage > 0.0 and action_damage_multiplier != 1.0:
            damage *= action_damage_multiplier
            detail["damage"] = damage
            detail["mechanic_damage_multiplier"] = action_damage_multiplier
            for key in (
                "target_damage_taken_amp_bonus_damage",
                "lynae_tune_strain_damage_amp_bonus_damage",
                "damage_before_lynae_tune_strain_amp",
                "damage_after_lynae_tune_strain_amp",
                "tune_break_damage_before_lynae_tune_strain_amp",
                "tune_break_damage_after_lynae_tune_strain_amp",
                "normal_damage_before_target_amp",
                "normal_damage_after_target_amp",
                "tune_break_damage_before_target_amp",
                "tune_break_damage_after_target_amp",
                "tune_break_damage",
            ):
                if key in detail:
                    detail[key] = float(detail.get(key, 0.0) or 0.0) * action_damage_multiplier
        hit_combat_offset = _hit_combat_offset(
            hit,
            action_time=action_time,
            combat_time_cost=combat_time_cost,
            untimed_fallback=not has_explicit_hit_timing,
        )
        hit_combat_time = combat_start_time + hit_combat_offset
        if detail:
            detail["hit_combat_offset"] = hit_combat_offset
            detail["hit_combat_time"] = hit_combat_time
        excluded_by_cutoff = (
            combat_duration is not None
            and hit_combat_time > combat_duration + 1e-9
        )
        if truncated_by_combat_limit and not has_explicit_hit_timing:
            excluded_by_cutoff = True
        if excluded_by_cutoff:
            damage_after_cutoff_excluded += damage
            continue
        if detail:
            hit_details.append(detail)
            amp_bonus_damage = float(detail.get("target_damage_taken_amp_bonus_damage", 0.0) or 0.0)
            direct_damage_taken_amp_total_bonus_damage += amp_bonus_damage
            lynae_bonus_damage = float(detail.get("lynae_tune_strain_damage_amp_bonus_damage", 0.0) or 0.0)
            lynae_tune_strain_damage_amp_bonus_damage += lynae_bonus_damage
            if lynae_bonus_damage > 0.0:
                lynae_tune_strain_damage_amp = float(detail.get("lynae_tune_strain_damage_amp", 0.0) or 0.0)
                lynae_tune_strain_damage_multiplier = float(
                    detail.get("lynae_tune_strain_damage_multiplier", 1.0) or 1.0
                )
                lynae_tune_strain_source_status = detail.get("lynae_tune_strain_source_status")
                lynae_tune_strain_source_ref = detail.get("lynae_tune_strain_source_ref")
            if detail.get("interfered_marker_amp_applied_to_direct_damage"):
                interfered_marker_direct_damage_amp_applied_count += 1
            if detail.get("tune_break_damage_receives_existing_interfered_marker_amp"):
                interfered_marker_direct_damage_amp_applied_count += 1
                tune_break_damage_receives_existing_interfered_marker_amp = True
            if detail.get("tune_break_damage_receives_newly_applied_interfered_marker_amp"):
                tune_break_damage_receives_newly_applied_interfered_marker_amp = True
            tune_break_damage_before_target_amp += float(detail.get("tune_break_damage_before_target_amp", 0.0) or 0.0)
            tune_break_damage_after_target_amp += float(detail.get("tune_break_damage_after_target_amp", 0.0) or 0.0)
            if not action_damage_bonus_context and "effective_damage_bonus" in detail:
                action_damage_bonus_context = {
                    key: detail.get(key)
                    for key in (
                        "damage_category",
                        "damage_bonus_category",
                        "damage_element",
                        "raw_skill_category",
                        "raw_damage_type",
                        "all_dmg_bonus",
                        "category_dmg_bonus",
                        "element_dmg_bonus",
                        "runtime_element_damage_bonus",
                        "echo_set_damage_bonus",
                        "effective_damage_bonus",
                        "crit_rate_before_buffs",
                        "crit_rate_after_buffs",
                        "crit_damage_before_buffs",
                        "crit_damage_after_buffs",
                        "runtime_crit_damage_bonus",
                        "starfield_calibrator_party_crit_damage_active",
                        "starfield_calibrator_party_crit_damage_bonus",
                        "everbright_polestar_all_attribute_bonus_active",
                        "everbright_polestar_all_attribute_damage_bonus",
                        "runtime_all_attribute_damage_bonus",
                        "element_damage_bonus_before_weapon",
                        "element_damage_bonus_after_weapon",
                        "everbright_polestar_liberation_penetration_active",
                        "everbright_polestar_liberation_penetration_remaining",
                        "def_ignore_before_weapon",
                        "everbright_polestar_def_ignore_bonus",
                        "total_def_ignore",
                        "def_multiplier_before_weapon",
                        "def_multiplier_after_weapon",
                        "enemy_res_before_weapon",
                        "everbright_polestar_fusion_res_ignore_bonus",
                        "enemy_res_after_weapon",
                        "res_multiplier_before_weapon",
                        "res_multiplier_after_weapon",
                        "damage_element_fallback_used_for_weapon_res_ignore",
                        "build_profile_id",
                        "scaling_stat",
                        "scaling_value",
                        "stat_component_source",
                        "profile_completeness_status",
                        "implementation_status",
                        *stat_component_log_fields(detail).keys(),
                        *support_stat_log_fields(detail).keys(),
                        "halo_of_starry_radiance_5set_active",
                        "halo_of_starry_radiance_5set_atk_percent_bonus",
                        "high_syntony_field_def_bonus_active",
                        "high_syntony_field_def_percent_bonus",
                        "high_syntony_field_off_tune_inherited",
                        "high_syntony_field_heal_proxy_active",
                        "high_syntony_field_healing_multiplier_bonus",
                        "high_syntony_field_healing_multiplier_metadata_only",
                        "critical_protocol_high_syntony_created_before_damage",
                        "high_syntony_field_same_action_application",
                        "high_syntony_field_application_timing",
                        "halo_atk_buff_does_not_affect_mornye_def_damage",
                        "halo_of_starry_radiance_5set_applied_before_field_creation_damage",
                        "halo_of_starry_radiance_5set_same_action_application",
                        "halo_of_starry_radiance_5set_application_timing",
                    )
                }
                action_damage_bonus_context["damage_category"] = action_damage_bonus_context.get("damage_category") or "other"
                action_damage_bonus_context["damage_bonus_category"] = (
                    action_damage_bonus_context.get("damage_bonus_category")
                    or action_damage_bonus_context.get("damage_category")
                    or "other"
                )
                action_damage_bonus_context["damage_element"] = action_damage_bonus_context.get("damage_element") or "generic"
        damage_by_category[hit.damage_category] = damage_by_category.get(hit.damage_category, 0.0) + damage
        if hit.damage_category == "normal":
            normal_damage += damage
        elif hit.damage_category == "tune_break":
            tune_break_damage += damage

    direct_amp_summary = {
        "direct_damage_taken_amp_total_bonus_damage": direct_damage_taken_amp_total_bonus_damage,
        "interfered_marker_direct_damage_amp_applied_count": interfered_marker_direct_damage_amp_applied_count,
        "interfered_marker_direct_damage_amp_bonus_damage": direct_damage_taken_amp_total_bonus_damage,
        "interfered_marker_direct_damage_amp_source_ref": (
            INTERFERED_MARKER_AMP_SOURCE_REF if interfered_marker_direct_damage_amp_applied_count else None
        ),
        "tune_break_damage_receives_existing_interfered_marker_amp": (
            tune_break_damage_receives_existing_interfered_marker_amp
        ),
        "tune_break_damage_receives_newly_applied_interfered_marker_amp": (
            tune_break_damage_receives_newly_applied_interfered_marker_amp
        ),
        "tune_break_damage_before_target_amp": tune_break_damage_before_target_amp,
        "tune_break_damage_after_target_amp": tune_break_damage_after_target_amp,
        "lynae_tune_strain_damage_amp_bonus_damage": lynae_tune_strain_damage_amp_bonus_damage,
        "lynae_tune_strain_damage_amp": lynae_tune_strain_damage_amp,
        "lynae_tune_strain_damage_multiplier": lynae_tune_strain_damage_multiplier,
        "lynae_tune_strain_source_status": lynae_tune_strain_source_status,
        "lynae_tune_strain_source_ref": lynae_tune_strain_source_ref,
    }

    return (
        normal_damage,
        tune_break_damage,
        hit_details,
        damage_by_category,
        damage_after_cutoff_excluded,
        action_damage_bonus_context,
        direct_amp_summary,
    )


def _action_has_trigger_damage_potential(action: ActionData, action_time: float) -> bool:
    if action.character_id is None:
        return False
    for hit in _resolved_action_hits(action, action_time=action_time):
        if hit.time > action_time:
            continue
        if hit.damage_category == "normal" and hit.damage_multiplier > 0.0:
            return True
        if hit.damage_category == "tune_break" and hit.tune_break_multiplier > 0.0:
            return True
    return False


def _sync_hit_detail_runtime_event_logs(
    hit_details: list[dict],
    echo_set_log_fields: dict[str, Any],
    mechanic_event_log_fields: dict[str, Any],
) -> None:
    event_fields = {
        "emitted_mechanic_event_tags": list(mechanic_event_log_fields.get("emitted_mechanic_event_tags", [])),
        "mechanic_event_triggered": bool(mechanic_event_log_fields.get("mechanic_event_triggered", False)),
        "mechanic_event_trigger_id": mechanic_event_log_fields.get("mechanic_event_trigger_id"),
        "mechanic_event_cooldown_blocked": bool(mechanic_event_log_fields.get("mechanic_event_cooldown_blocked", False)),
        "aemeath_resonance_mode": mechanic_event_log_fields.get("aemeath_resonance_mode"),
        "mechanic_event_source_status": mechanic_event_log_fields.get("mechanic_event_source_status"),
        "mechanic_event_unresolved_reason": mechanic_event_log_fields.get("mechanic_event_unresolved_reason"),
        "echo_set_triggered_buff_ids": list(echo_set_log_fields.get("echo_set_triggered_buff_ids", [])),
        "echo_set_buff_refreshed": bool(echo_set_log_fields.get("echo_set_buff_refreshed", False)),
        "aemeath_trailblazing_star_5set_applied_before_triggering_damage": bool(
            echo_set_log_fields.get("aemeath_trailblazing_star_5set_applied_before_triggering_damage", False)
        ),
        "trailblazing_star_5set_same_action_application": bool(
            echo_set_log_fields.get("trailblazing_star_5set_same_action_application", False)
        ),
        "trailblazing_star_5set_application_timing": echo_set_log_fields.get(
            "trailblazing_star_5set_application_timing"
        ),
        "team_heal_event_triggered": bool(echo_set_log_fields.get("team_heal_event_triggered", False)),
        "mornye_heal_event_mode": echo_set_log_fields.get("mornye_heal_event_mode"),
        "high_syntony_field_active": bool(echo_set_log_fields.get("high_syntony_field_active", False)),
        "high_syntony_field_remaining": float(echo_set_log_fields.get("high_syntony_field_remaining", 0.0) or 0.0),
        "high_syntony_field_created_count": int(echo_set_log_fields.get("high_syntony_field_created_count", 0) or 0),
        "high_syntony_field_def_bonus_active": bool(
            echo_set_log_fields.get("high_syntony_field_def_bonus_active", False)
        ),
        "high_syntony_field_def_percent_bonus": float(
            echo_set_log_fields.get("high_syntony_field_def_percent_bonus", 0.0) or 0.0
        ),
        "high_syntony_field_off_tune_inherited": bool(
            echo_set_log_fields.get("high_syntony_field_off_tune_inherited", False)
        ),
        "high_syntony_field_heal_proxy_active": bool(
            echo_set_log_fields.get("high_syntony_field_heal_proxy_active", False)
        ),
        "high_syntony_field_healing_multiplier_bonus": float(
            echo_set_log_fields.get("high_syntony_field_healing_multiplier_bonus", 0.0) or 0.0
        ),
        "high_syntony_field_healing_multiplier_metadata_only": bool(
            echo_set_log_fields.get("high_syntony_field_healing_multiplier_metadata_only", True)
        ),
        "critical_protocol_high_syntony_created_before_damage": bool(
            echo_set_log_fields.get("critical_protocol_high_syntony_created_before_damage", False)
        ),
        "high_syntony_field_same_action_application": bool(
            echo_set_log_fields.get("high_syntony_field_same_action_application", False)
        ),
        "high_syntony_field_application_timing": echo_set_log_fields.get("high_syntony_field_application_timing"),
        "high_syntony_field_unavailable_reason": echo_set_log_fields.get("high_syntony_field_unavailable_reason"),
        "halo_atk_buff_does_not_affect_mornye_def_damage": bool(
            echo_set_log_fields.get("halo_atk_buff_does_not_affect_mornye_def_damage", False)
        ),
        "halo_of_starry_radiance_5set_applied_before_field_creation_damage": bool(
            echo_set_log_fields.get("halo_of_starry_radiance_5set_applied_before_field_creation_damage", False)
        ),
        "halo_of_starry_radiance_5set_same_action_application": bool(
            echo_set_log_fields.get("halo_of_starry_radiance_5set_same_action_application", False)
        ),
        "halo_of_starry_radiance_5set_application_timing": echo_set_log_fields.get(
            "halo_of_starry_radiance_5set_application_timing"
        ),
        "halo_of_starry_radiance_5set_unavailable_reason": echo_set_log_fields.get(
            "halo_of_starry_radiance_5set_unavailable_reason"
        ),
    }
    for detail in hit_details:
        event_fields["high_syntony_field_def_bonus_active"] = bool(
            echo_set_log_fields.get("high_syntony_field_def_bonus_active", False)
            or detail.get("high_syntony_field_def_bonus_active", False)
        )
        event_fields["high_syntony_field_def_percent_bonus"] = max(
            float(echo_set_log_fields.get("high_syntony_field_def_percent_bonus", 0.0) or 0.0),
            float(detail.get("high_syntony_field_def_percent_bonus", 0.0) or 0.0),
        )
        event_fields["high_syntony_field_off_tune_inherited"] = bool(
            echo_set_log_fields.get("high_syntony_field_off_tune_inherited", False)
            or detail.get("high_syntony_field_off_tune_inherited", False)
        )
        event_fields["halo_atk_buff_does_not_affect_mornye_def_damage"] = bool(
            echo_set_log_fields.get("halo_atk_buff_does_not_affect_mornye_def_damage", False)
            or detail.get("halo_atk_buff_does_not_affect_mornye_def_damage", False)
        )
        event_fields["halo_of_starry_radiance_5set_active"] = bool(
            echo_set_log_fields.get(
                "halo_of_starry_radiance_5set_active",
                detail.get("halo_of_starry_radiance_5set_active", False),
            )
        )
        event_fields["halo_of_starry_radiance_5set_atk_percent_bonus"] = float(
            echo_set_log_fields.get(
                "halo_of_starry_radiance_5set_atk_percent_bonus",
                detail.get("halo_of_starry_radiance_5set_atk_percent_bonus", 0.0),
            )
            or 0.0
        )
        detail.update(event_fields)


def execute_action(
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    mechanic: Any | None = None,
    combat_duration: float | None = None,
    pre_action_echo_set_log_fields: dict[str, Any] | None = None,
    weapon_definitions: dict[str, Any] | None = None,
    scheduled_effect_runner: Any | None = None,
) -> ActionResult:
    valid, reason = is_action_valid(action, state)
    start_time = state.current_time
    combat_start_time = state.combat_time
    active_character_before = state.active_character_id
    transition_actor_character_id = (action.mechanic_effects or {}).get("transition_actor_character_id")
    actor_character_id = (
        str(transition_actor_character_id)
        if transition_actor_character_id
        else active_character_before
        if action.action_type in {"swap", "wait"}
        else action.character_id
    )
    actor_character_id = actor_character_id or active_character_before
    actor_state = state.character_mechanics_state.get(action.character_id or state.active_character_id, {})
    _duration, action_time, combat_time_cost = resolve_action_runtime_timing(action, actor_state)
    if combat_duration is not None and combat_start_time >= combat_duration:
        valid = False
        reason = "Combat duration has ended."
    combat_time_end, effective_combat_time_cost, truncated_by_combat_limit = combat_time_cutoff(
        combat_start_time,
        combat_time_cost,
        combat_duration,
    )
    if not valid:
        return ActionResult(
            action_id=action.id,
            action_name=action.name,
            character_id=action.character_id,
            actor_character_id=actor_character_id,
            active_character_before=active_character_before,
            active_character_after=state.active_character_id,
            start_time=start_time,
            end_time=start_time,
            action_time=0.0,
            action_type=action.action_type,
            combat_time_start=combat_start_time,
            combat_time_end=combat_start_time,
            combat_time_cost=0.0,
            effective_combat_time_cost=0.0,
            truncated_by_combat_limit=False,
            damage_before_cutoff=0.0,
            damage_after_cutoff_excluded=0.0,
            damage=0.0,
            valid=False,
            reason=reason,
        )

    if mechanic is not None:
        mechanic.before_action(state, action)
    action_damage_multiplier = (
        mechanic.get_action_damage_multiplier(state, action)
        if mechanic is not None
        else 1.0
    )
    temporary_stat_modifiers = (
        mechanic.get_action_stat_modifiers(state, action, characters)
        if mechanic is not None and hasattr(mechanic, "get_action_stat_modifiers")
        else {}
    )
    mechanic_log_fields = (
        mechanic.get_action_log_fields(state, action, characters)
        if mechanic is not None and hasattr(mechanic, "get_action_log_fields")
        else {}
    )
    mechanic_log_fields = dict(mechanic_log_fields)

    echo_set_log_fields = merge_echo_set_logs(echo_set_base_log_fields(), pre_action_echo_set_log_fields or {})
    pre_damage_event_preview = preview_mechanic_event_trigger(
        action,
        state,
        action_start_combat_time=combat_start_time,
    )
    if (
        not truncated_by_combat_limit
        and pre_damage_event_preview.get("emitted_mechanic_event_tags")
        and _action_has_trigger_damage_potential(action, action_time)
    ):
        echo_set_log_fields = merge_echo_set_logs(
            echo_set_log_fields,
            apply_echo_set_event_buffs(
            actor_character_id=actor_character_id,
            emitted_event_tags=pre_damage_event_preview.get("emitted_mechanic_event_tags", []),
            characters=characters,
            state=state,
            buffs=buffs,
            application_time=combat_start_time,
            applied_before_triggering_damage=True,
            ),
        )

    action_start_snapshot = capture_action_start_effect_snapshot(state)
    force_active_buff_ids: set[str] = set(action_start_snapshot.active_buff_ids)
    if echo_set_log_fields.get("halo_of_starry_radiance_5set_same_action_application"):
        force_active_buff_ids.add(MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID)
    if echo_set_log_fields.get("high_syntony_field_same_action_application"):
        force_active_buff_ids.add(MORNYE_HIGH_SYNTONY_FIELD_DEF_BUFF_ID)
        force_active_buff_ids.add(MORNYE_HIGH_SYNTONY_FIELD_OFF_TUNE_BUFF_ID)

    # Damage events use an action-start state snapshot. Trailblazing Star 5-set is
    # pre-applied for same-action trigger damage; other action-applied buffs and
    # anomalies are added after action_time and affect later actions only.
    (
        normal_damage,
        tune_break_damage,
        hit_details,
        hit_damage_by_category,
        damage_after_cutoff_excluded,
        action_damage_bonus_context,
        direct_amp_summary,
    ) = _calculate_hit_damage_totals(
        action,
        state,
        characters,
        buffs,
        action_time=action_time,
        combat_time_cost=combat_time_cost,
        combat_start_time=combat_start_time,
        combat_duration=combat_duration,
        truncated_by_combat_limit=truncated_by_combat_limit,
        action_damage_multiplier=action_damage_multiplier,
        temporary_stat_modifiers=temporary_stat_modifiers,
        force_active_buff_ids=force_active_buff_ids,
        action_start_snapshot=action_start_snapshot,
        weapon_definitions=weapon_definitions,
    )
    direct_damage = normal_damage + tune_break_damage
    mechanic_event_log_fields = process_mechanic_event_triggers(
        action,
        state,
        direct_damage=direct_damage,
        action_start_combat_time=combat_start_time,
    )
    _sync_hit_detail_runtime_event_logs(hit_details, echo_set_log_fields, mechanic_event_log_fields)

    generated_packets = (
        mechanic.get_generated_damage_packets(
            state,
            action,
            action_time=action_time,
            combat_time_cost=combat_time_cost,
            combat_start_time=combat_start_time,
            characters=characters,
            buffs=buffs,
            force_active_buff_ids=force_active_buff_ids,
            mechanic_event_log_fields=mechanic_event_log_fields,
            echo_set_log_fields=echo_set_log_fields,
            weapon_definitions=weapon_definitions or {},
        )
        if mechanic is not None and hasattr(mechanic, "get_generated_damage_packets")
        else []
    )
    generated_mechanic_damage = 0.0
    generated_mechanic_events: list[dict[str, Any]] = []
    generated_mechanic_hit_count = 0
    generated_lynae_tune_strain_damage_amp_bonus_damage = 0.0
    for packet in generated_packets:
        packet_damage, packet_details = calculate_generated_damage_packet(
            packet,
            source_action=action,
            state=state,
            characters=characters,
            buffs=buffs,
            force_active_buff_ids=force_active_buff_ids,
            action_start_snapshot=action_start_snapshot,
        )
        event = {
            "id": packet.id,
            "name": packet.name,
            "source_character_id": packet.source_character_id,
            "source_action_id": packet.source_action_id,
            "formula_type": packet.formula_type,
            "source_status": packet.source_status,
            "source_ref": packet.source_ref,
            "source_rows": list(packet.source_rows),
            "repeat_count": packet.repeat_count,
            "source_multiplier": packet.source_multiplier if packet.source_multiplier is not None else packet.tune_multiplier,
            "tune_multiplier": packet.tune_multiplier,
            "variant": packet.variant,
            "hit_interval_frames": packet.hit_interval_frames,
            "runtime_applicable": packet.runtime_applicable,
            "damage": packet_damage,
            "notes": packet.notes,
        }
        if packet.source_character_id == "aemeath" and packet.id.startswith("aemeath_seraphic_duet"):
            aemeath_state = state.character_mechanics_state.get("aemeath", {})
            event.update(
                {
                    "trail_stack_snapshot": int(
                        aemeath_state.get("last_seraphic_duet_trail_stack_snapshot", 0) or 0
                    ),
                    "trail_stack_factor": float(
                        aemeath_state.get("last_seraphic_duet_trail_stack_factor", 1.0) or 1.0
                    ),
                    "trail_preservation_active": bool(
                        aemeath_state.get("last_seraphic_duet_trail_preservation_active", False)
                    ),
                    "trail_consumed": bool(aemeath_state.get("last_seraphic_duet_trail_consumed", False)),
                    "stacks_after": int(getattr(state, "rupturous_trail_stacks", 0) or 0),
                    "trail_stacks_after": int(getattr(state, "rupturous_trail_stacks", 0) or 0),
                    "trail_preservation_after": bool(
                        aemeath_state.get("last_seraphic_duet_trail_preservation_after", False)
                    ),
                    "stack_bonus_per_stack": 0.04,
                    "base_multiplier_per_hit": 1.0935,
                    "total_extra_tune_multiplier": float(
                        aemeath_state.get("last_seraphic_duet_total_extra_tune_multiplier", 0.0) or 0.0
                    ),
                }
            )
        packet_lynae_tune_strain_bonus = sum(
            float(detail.get("lynae_tune_strain_damage_amp_bonus_damage", 0.0) or 0.0)
            for detail in packet_details
        )
        if packet_lynae_tune_strain_bonus > 0.0:
            first_amp_detail = next(
                (
                    detail
                    for detail in packet_details
                    if float(detail.get("lynae_tune_strain_damage_amp_bonus_damage", 0.0) or 0.0) > 0.0
                ),
                {},
            )
            event.update(
                {
                    "lynae_tune_strain_damage_amp_bonus_damage": packet_lynae_tune_strain_bonus,
                    "lynae_tune_strain_damage_amp": float(
                        first_amp_detail.get("lynae_tune_strain_damage_amp", 0.0) or 0.0
                    ),
                    "lynae_tune_strain_damage_multiplier": float(
                        first_amp_detail.get("lynae_tune_strain_damage_multiplier", 1.0) or 1.0
                    ),
                    "lynae_tune_strain_source_status": first_amp_detail.get("lynae_tune_strain_source_status"),
                    "lynae_tune_strain_source_ref": first_amp_detail.get("lynae_tune_strain_source_ref"),
                }
            )
            generated_lynae_tune_strain_damage_amp_bonus_damage += packet_lynae_tune_strain_bonus
        generated_mechanic_events.append(event)
        if packet_damage <= 0.0:
            continue
        generated_mechanic_damage += packet_damage
        generated_mechanic_hit_count += len(packet_details)
        for detail in packet_details:
            hit_details.append(detail)
            category = str(detail.get("damage_category") or packet.formula_type)
            hit_damage_by_category[category] = hit_damage_by_category.get(category, 0.0) + float(
                detail.get("damage", 0.0) or 0.0
            )
    if generated_lynae_tune_strain_damage_amp_bonus_damage > 0.0:
        direct_amp_summary["lynae_tune_strain_damage_amp_bonus_damage"] = float(
            direct_amp_summary.get("lynae_tune_strain_damage_amp_bonus_damage", 0.0) or 0.0
        ) + generated_lynae_tune_strain_damage_amp_bonus_damage
        direct_amp_summary["lynae_tune_strain_damage_amp"] = state.lynae_tune_strain_damage_amp
        direct_amp_summary["lynae_tune_strain_damage_multiplier"] = state.lynae_tune_strain_damage_multiplier
        direct_amp_summary["lynae_tune_strain_source_status"] = state.lynae_tune_strain_source_status
        direct_amp_summary["lynae_tune_strain_source_ref"] = state.lynae_tune_strain_source_ref
    if generated_mechanic_events:
        mechanic_log_fields.update(
            {
                "generated_mechanic_damage": generated_mechanic_damage,
                "generated_mechanic_damage_total": generated_mechanic_damage,
                "generated_mechanic_hit_count": generated_mechanic_hit_count,
                "generated_mechanic_damage_events": generated_mechanic_events,
            }
        )
    if action.character_id == "aemeath" and action.id in {"aemeath_seraphic_duet_overturn", "aemeath_seraphic_duet_encore"}:
        aemeath_state = state.character_mechanics_state.get("aemeath", {})
        packet_source_rows = sorted(
            {
                int(row)
                for event in generated_mechanic_events
                for row in event.get("source_rows", [])
            }
        )
        source_status = (
            "workbook_confirmed"
            if generated_mechanic_damage > 0.0
            else "unresolved_no_runtime_effect"
            if generated_mechanic_events
            else None
        )
        mechanic_log_fields.update(
            {
                "aemeath_forte_generated_damage": generated_mechanic_damage,
                "aemeath_forte_generated_damage_total": generated_mechanic_damage,
                "aemeath_seraphic_duet_followup_triggered": generated_mechanic_damage > 0.0,
                "aemeath_seraphic_duet_followup_damage": generated_mechanic_damage,
                "aemeath_seraphic_duet_followup_source_status": source_status,
                "aemeath_seraphic_duet_followup_mode": (
                    "tune_rupture"
                    if any("tune_rupture" in event.get("id", "") for event in generated_mechanic_events)
                    else None
                ),
                "aemeath_seraphic_duet_followup_variant": aemeath_state.get("last_seraphic_duet_followup_variant"),
                "aemeath_seraphic_duet_followup_repeat_count": int(
                    aemeath_state.get("last_seraphic_duet_followup_repeat_count", 0) or 0
                ),
                "aemeath_seraphic_duet_followup_multiplier": float(
                    aemeath_state.get("last_seraphic_duet_followup_multiplier", 0.0) or 0.0
                ),
                "aemeath_seraphic_duet_trail_stack_snapshot": int(
                    aemeath_state.get("last_seraphic_duet_trail_stack_snapshot", 0) or 0
                ),
                "aemeath_seraphic_duet_trail_stack_factor": float(
                    aemeath_state.get("last_seraphic_duet_trail_stack_factor", 1.0) or 1.0
                ),
                "aemeath_seraphic_duet_trail_preservation_active": bool(
                    aemeath_state.get("last_seraphic_duet_trail_preservation_active", False)
                ),
                "aemeath_seraphic_duet_trail_preservation_after": bool(
                    aemeath_state.get("last_seraphic_duet_trail_preservation_after", False)
                ),
                "aemeath_seraphic_duet_trail_consumed": bool(
                    aemeath_state.get("last_seraphic_duet_trail_consumed", False)
                ),
                "aemeath_seraphic_duet_total_extra_tune_multiplier": float(
                    aemeath_state.get("last_seraphic_duet_total_extra_tune_multiplier", 0.0) or 0.0
                ),
                "aemeath_rupturous_trail_stacks_before": int(
                    aemeath_state.get("last_seraphic_duet_trail_stack_snapshot", 0) or 0
                ),
                "aemeath_rupturous_trail_stacks_consumed": int(
                    aemeath_state.get("last_seraphic_duet_consumed_rupturous_trail_stacks", 0) or 0
                ),
                "aemeath_rupturous_trail_stacks_after": int(getattr(state, "rupturous_trail_stacks", 0) or 0),
                "aemeath_forte_enhancement_stacks_before": int(
                    aemeath_state.get("last_seraphic_duet_forte_enhancement_stacks_before", 0) or 0
                ),
                "aemeath_forte_enhancement_stacks_consumed": int(
                    aemeath_state.get("last_seraphic_duet_forte_enhancement_stacks_consumed", 0) or 0
                ),
                "aemeath_forte_enhancement_stacks_after": int(
                    aemeath_state.get("last_seraphic_duet_forte_enhancement_stacks_after", 0) or 0
                ),
                "aemeath_trail_no_cost_consumed": bool(
                    aemeath_state.get("last_seraphic_duet_trail_no_cost_consumed", False)
                ),
                "aemeath_stardust_resonance_active_for_followup": float(
                    aemeath_state.get("stardust_resonance_remaining", 0.0) or 0.0
                )
                > 0.0,
                "aemeath_seraphic_duet_followup_source_rows": packet_source_rows,
            }
        )

    scheduled_effect_result = (
        scheduled_effect_runner(
            combat_start_time=combat_start_time,
            combat_elapsed=effective_combat_time_cost,
            action_start_snapshot=action_start_snapshot,
            force_active_buff_ids=set(force_active_buff_ids),
        )
        if scheduled_effect_runner is not None
        else {}
    )
    scheduled_damage = float(scheduled_effect_result.get("scheduled_damage", 0.0) or 0.0)
    scheduled_damage_events = list(scheduled_effect_result.get("scheduled_damage_events", []))
    scheduled_healing_events = list(scheduled_effect_result.get("scheduled_healing_events", []))
    scheduled_status_application_events = list(
        scheduled_effect_result.get("scheduled_status_application_events", [])
    )

    if action.action_type == "swap" and action.character_id is not None:
        state.active_character_id = action.character_id

    state.total_damage += direct_damage + generated_mechanic_damage + scheduled_damage
    resource_change = None if truncated_by_combat_limit else apply_resource_changes(state, action, characters)

    state.current_time += action_time
    state.combat_time = combat_time_end
    reduce_cooldowns(state, effective_combat_time_cost)
    tick_buffs(state, effective_combat_time_cost)
    anomaly_tick_damage, anomaly_damage_by_type = advance_anomalies(state, effective_combat_time_cost)
    if truncated_by_combat_limit:
        damage_after_cutoff_excluded += anomaly_tick_damage
        anomaly_tick_damage = 0.0
        anomaly_damage_by_type = {}
    state.total_damage += anomaly_tick_damage

    total_action_damage = direct_damage + generated_mechanic_damage + scheduled_damage + anomaly_tick_damage

    if not truncated_by_combat_limit:
        for buff_id in action.applies_buffs:
            apply_buff(state, buffs[buff_id], action.character_id)
        apply_anomaly(state, action)

    # Simplified cooldown model: cooldown starts at the end of the action.
    if action.cooldown > 0.0 and not truncated_by_combat_limit:
        state.cooldowns[cooldown_key(action)] = action.cooldown

    active_anomalies_after = {
        anomaly_type: anomaly.stacks
        for anomaly_type, anomaly in state.active_anomalies.items()
        if anomaly.remaining_duration > 0.0
    }
    active_buff_ids = [buff.buff_id for buff in state.active_buffs if buff.remaining_duration > 0.0]
    applied_buff_ids = list(action.applies_buffs) if not truncated_by_combat_limit else []

    profile_implementation_status = action_damage_bonus_context.get("implementation_status")
    if "implementation_status" not in mechanic_log_fields:
        mechanic_log_fields["implementation_status"] = profile_implementation_status
    support_log_fields = support_stat_log_fields(action_damage_bonus_context)
    for key in tuple(support_log_fields):
        if key in echo_set_log_fields:
            if support_log_fields[key] in (None, False, 0, 0.0):
                support_log_fields[key] = echo_set_log_fields[key]
    explicit_result_log_keys = {
        "high_syntony_field_active",
        "high_syntony_field_remaining",
        "high_syntony_field_created_count",
        "high_syntony_field_def_bonus_active",
        "high_syntony_field_def_percent_bonus",
        "high_syntony_field_off_tune_inherited",
        "high_syntony_field_heal_proxy_active",
        "high_syntony_field_healing_multiplier_bonus",
        "high_syntony_field_healing_multiplier_metadata_only",
        "critical_protocol_high_syntony_created_before_damage",
        "high_syntony_field_same_action_application",
        "high_syntony_field_application_timing",
        "high_syntony_field_unavailable_reason",
        "halo_atk_buff_does_not_affect_mornye_def_damage",
        "source_status",
        "implementation_status",
        "profile_completeness_status",
        "build_profile_id",
        "weapon_effects_enabled",
        "weapon_effect_triggered",
        "weapon_effect_logs",
        "weapon_effect_trigger_counts",
        "weapon_effect_cooldown_blocked_counts",
        "weapon_id",
        "weapon_rank",
        "weapon_effect_id",
        "weapon_effect_type",
        "weapon_effect_resource",
        "weapon_effect_source_status",
        "concerto_energy_before_weapon_effect",
        "concerto_energy_restored_by_weapon",
        "concerto_energy_after_weapon_effect",
        "concerto_energy_wasted_by_weapon",
        "weapon_effect_cooldown_seconds",
        "weapon_effect_cooldown_remaining",
        "weapon_effect_cooldown_blocked",
        "weapon_effect_buff_refreshed",
        "weapon_effect_duration_seconds",
        "starfield_calibrator_party_crit_damage_active",
        "starfield_calibrator_party_crit_damage_bonus",
        "everbright_polestar_all_attribute_bonus_active",
        "everbright_polestar_all_attribute_damage_bonus",
        "runtime_all_attribute_damage_bonus",
        "element_damage_bonus_before_weapon",
        "element_damage_bonus_after_weapon",
        "everbright_polestar_liberation_penetration_active",
        "everbright_polestar_liberation_penetration_remaining",
        "def_ignore_before_weapon",
        "everbright_polestar_def_ignore_bonus",
        "total_def_ignore",
        "def_multiplier_before_weapon",
        "def_multiplier_after_weapon",
        "enemy_res_before_weapon",
        "everbright_polestar_fusion_res_ignore_bonus",
        "enemy_res_after_weapon",
        "res_multiplier_before_weapon",
        "res_multiplier_after_weapon",
        "damage_element_fallback_used_for_weapon_res_ignore",
    }
    echo_set_result_log_fields = {
        key: value
        for key, value in echo_set_log_fields.items()
        if key not in support_log_fields and key not in explicit_result_log_keys
    }
    weapon_effect_logs = list(echo_set_log_fields.get("weapon_effect_logs", []))
    primary_weapon_log = weapon_effect_logs[0] if weapon_effect_logs else {}
    for generated_key in (
        "generated_mechanic_damage",
        "generated_mechanic_damage_total",
        "generated_mechanic_hit_count",
        "generated_mechanic_damage_events",
    ):
        mechanic_log_fields.pop(generated_key, None)

    result = ActionResult(
        action_id=action.id,
        action_name=action.name,
        character_id=action.character_id,
        actor_character_id=actor_character_id,
        active_character_before=active_character_before,
        active_character_after=state.active_character_id,
        start_time=start_time,
        end_time=state.current_time,
        action_time=action_time,
        combat_time_start=combat_start_time,
        combat_time_end=state.combat_time,
        combat_time_cost=combat_time_cost,
        effective_combat_time_cost=effective_combat_time_cost,
        truncated_by_combat_limit=truncated_by_combat_limit,
        damage_before_cutoff=total_action_damage,
        damage_after_cutoff_excluded=damage_after_cutoff_excluded,
        damage=total_action_damage,
        normal_damage=normal_damage,
        tune_break_damage=tune_break_damage,
        direct_action_damage=direct_damage + generated_mechanic_damage + anomaly_tick_damage,
        scheduled_damage=scheduled_damage,
        scheduled_damage_events=scheduled_damage_events,
        scheduled_healing_events=scheduled_healing_events,
        scheduled_status_application_events=scheduled_status_application_events,
        direct_damage_taken_amp_total_bonus_damage=float(
            direct_amp_summary.get("direct_damage_taken_amp_total_bonus_damage", 0.0) or 0.0
        ),
        interfered_marker_direct_damage_amp_applied_count=int(
            direct_amp_summary.get("interfered_marker_direct_damage_amp_applied_count", 0) or 0
        ),
        interfered_marker_direct_damage_amp_bonus_damage=float(
            direct_amp_summary.get("interfered_marker_direct_damage_amp_bonus_damage", 0.0) or 0.0
        ),
        interfered_marker_direct_damage_amp_source_ref=direct_amp_summary.get(
            "interfered_marker_direct_damage_amp_source_ref"
        ),
        tune_break_damage_receives_existing_interfered_marker_amp=bool(
            direct_amp_summary.get("tune_break_damage_receives_existing_interfered_marker_amp", False)
        ),
        tune_break_damage_receives_newly_applied_interfered_marker_amp=bool(
            direct_amp_summary.get("tune_break_damage_receives_newly_applied_interfered_marker_amp", False)
        ),
        tune_break_damage_before_target_amp=float(
            direct_amp_summary.get("tune_break_damage_before_target_amp", 0.0) or 0.0
        ),
        tune_break_damage_after_target_amp=float(
            direct_amp_summary.get("tune_break_damage_after_target_amp", 0.0) or 0.0
        ),
        target_tune_strain_interfered_stacks=state.target_tune_strain_interfered_stacks,
        target_tune_strain_interfered_max_stacks=state.target_tune_strain_interfered_max_stacks,
        target_tune_strain_interfered_remaining=state.target_tune_strain_interfered_remaining,
        lynae_tune_strain_damage_amp=float(
            direct_amp_summary.get("lynae_tune_strain_damage_amp", state.lynae_tune_strain_damage_amp) or 0.0
        ),
        lynae_tune_strain_damage_multiplier=float(
            direct_amp_summary.get("lynae_tune_strain_damage_multiplier", state.lynae_tune_strain_damage_multiplier)
            or 1.0
        ),
        lynae_tune_strain_damage_amp_bonus_damage=float(
            direct_amp_summary.get("lynae_tune_strain_damage_amp_bonus_damage", 0.0) or 0.0
        ),
        lynae_tune_strain_source_status=(
            direct_amp_summary.get("lynae_tune_strain_source_status") or state.lynae_tune_strain_source_status
        ),
        lynae_tune_strain_source_ref=(
            direct_amp_summary.get("lynae_tune_strain_source_ref") or state.lynae_tune_strain_source_ref
        ),
        generated_mechanic_damage=generated_mechanic_damage,
        generated_mechanic_damage_total=generated_mechanic_damage,
        generated_mechanic_hit_count=generated_mechanic_hit_count,
        generated_mechanic_damage_events=generated_mechanic_events,
        direct_anomaly_damage=0.0,
        anomaly_tick_damage=anomaly_tick_damage,
        anomaly_damage=anomaly_tick_damage,
        anomaly_damage_by_type=anomaly_damage_by_type,
        total_action_damage=total_action_damage,
        total_damage_after=state.total_damage,
        hit_count=len(hit_details),
        hit_damage_by_category=hit_damage_by_category,
        hit_details=hit_details,
        action_type=action.action_type,
        damage_category=action_damage_bonus_context.get("damage_bonus_category", action_damage_bonus_context.get("damage_category", "other")),
        damage_bonus_category=action_damage_bonus_context.get("damage_bonus_category", action_damage_bonus_context.get("damage_category", "other")),
        damage_element=action_damage_bonus_context.get("damage_element", "generic"),
        raw_skill_category=action_damage_bonus_context.get("raw_skill_category"),
        raw_damage_type=action_damage_bonus_context.get("raw_damage_type"),
        all_dmg_bonus=float(action_damage_bonus_context.get("all_dmg_bonus", 0.0)),
        category_dmg_bonus=float(action_damage_bonus_context.get("category_dmg_bonus", 0.0)),
        element_dmg_bonus=float(action_damage_bonus_context.get("element_dmg_bonus", 0.0)),
        runtime_element_damage_bonus=float(action_damage_bonus_context.get("runtime_element_damage_bonus", 0.0)),
        echo_set_damage_bonus=float(action_damage_bonus_context.get("echo_set_damage_bonus", 0.0)),
        effective_damage_bonus=float(action_damage_bonus_context.get("effective_damage_bonus", 0.0)),
        crit_rate_before_buffs=float(action_damage_bonus_context.get("crit_rate_before_buffs", 0.0)),
        crit_rate_after_buffs=float(action_damage_bonus_context.get("crit_rate_after_buffs", 0.0)),
        crit_damage_before_buffs=float(action_damage_bonus_context.get("crit_damage_before_buffs", 0.0)),
        crit_damage_after_buffs=float(action_damage_bonus_context.get("crit_damage_after_buffs", 0.0)),
        runtime_crit_damage_bonus=float(action_damage_bonus_context.get("runtime_crit_damage_bonus", 0.0)),
        starfield_calibrator_party_crit_damage_active=bool(
            action_damage_bonus_context.get("starfield_calibrator_party_crit_damage_active", False)
            or echo_set_log_fields.get("starfield_calibrator_party_crit_damage_active", False)
        ),
        starfield_calibrator_party_crit_damage_bonus=float(
            action_damage_bonus_context.get(
                "starfield_calibrator_party_crit_damage_bonus",
                echo_set_log_fields.get("starfield_calibrator_party_crit_damage_bonus", 0.0),
            )
            or 0.0
        ),
        everbright_polestar_all_attribute_bonus_active=bool(
            action_damage_bonus_context.get("everbright_polestar_all_attribute_bonus_active", False)
        ),
        everbright_polestar_all_attribute_damage_bonus=float(
            action_damage_bonus_context.get("everbright_polestar_all_attribute_damage_bonus", 0.0) or 0.0
        ),
        runtime_all_attribute_damage_bonus=float(
            action_damage_bonus_context.get("runtime_all_attribute_damage_bonus", 0.0) or 0.0
        ),
        element_damage_bonus_before_weapon=float(
            action_damage_bonus_context.get("element_damage_bonus_before_weapon", 0.0) or 0.0
        ),
        element_damage_bonus_after_weapon=float(
            action_damage_bonus_context.get("element_damage_bonus_after_weapon", 0.0) or 0.0
        ),
        everbright_polestar_liberation_penetration_active=bool(
            action_damage_bonus_context.get("everbright_polestar_liberation_penetration_active", False)
        ),
        everbright_polestar_liberation_penetration_remaining=float(
            action_damage_bonus_context.get("everbright_polestar_liberation_penetration_remaining", 0.0) or 0.0
        ),
        def_ignore_before_weapon=float(action_damage_bonus_context.get("def_ignore_before_weapon", 0.0) or 0.0),
        everbright_polestar_def_ignore_bonus=float(
            action_damage_bonus_context.get("everbright_polestar_def_ignore_bonus", 0.0) or 0.0
        ),
        total_def_ignore=float(action_damage_bonus_context.get("total_def_ignore", 0.0) or 0.0),
        def_multiplier_before_weapon=float(action_damage_bonus_context.get("def_multiplier_before_weapon", 0.0) or 0.0),
        def_multiplier_after_weapon=float(action_damage_bonus_context.get("def_multiplier_after_weapon", 0.0) or 0.0),
        enemy_res_before_weapon=float(action_damage_bonus_context.get("enemy_res_before_weapon", 0.0) or 0.0),
        everbright_polestar_fusion_res_ignore_bonus=float(
            action_damage_bonus_context.get("everbright_polestar_fusion_res_ignore_bonus", 0.0) or 0.0
        ),
        enemy_res_after_weapon=float(action_damage_bonus_context.get("enemy_res_after_weapon", 0.0) or 0.0),
        res_multiplier_before_weapon=float(action_damage_bonus_context.get("res_multiplier_before_weapon", 0.0) or 0.0),
        res_multiplier_after_weapon=float(action_damage_bonus_context.get("res_multiplier_after_weapon", 0.0) or 0.0),
        damage_element_fallback_used_for_weapon_res_ignore=bool(
            action_damage_bonus_context.get("damage_element_fallback_used_for_weapon_res_ignore", False)
        ),
        build_profile_id=action_damage_bonus_context.get("build_profile_id"),
        scaling_stat=action_damage_bonus_context.get("scaling_stat"),
        scaling_value=float(action_damage_bonus_context.get("scaling_value") or 0.0),
        stat_component_source=action_damage_bonus_context.get("stat_component_source"),
        **stat_component_log_fields(action_damage_bonus_context),
        **support_log_fields,
        profile_completeness_status=action_damage_bonus_context.get("profile_completeness_status"),
        **mechanic_event_log_fields,
        **echo_set_result_log_fields,
        weapon_effects_enabled=bool(echo_set_log_fields.get("weapon_effects_enabled", False)),
        weapon_effect_triggered=bool(echo_set_log_fields.get("weapon_effect_triggered", False)),
        weapon_effect_logs=weapon_effect_logs,
        weapon_id=echo_set_log_fields.get("weapon_id") or primary_weapon_log.get("weapon_id"),
        weapon_rank=int((echo_set_log_fields.get("weapon_rank") or primary_weapon_log.get("weapon_rank", 0)) or 0),
        weapon_effect_id=echo_set_log_fields.get("weapon_effect_id") or primary_weapon_log.get("weapon_effect_id"),
        weapon_effect_type=echo_set_log_fields.get("weapon_effect_type") or primary_weapon_log.get("weapon_effect_type"),
        weapon_effect_resource=echo_set_log_fields.get(
            "weapon_effect_resource"
        )
        or primary_weapon_log.get("weapon_effect_resource"),
        weapon_effect_source_status=echo_set_log_fields.get("weapon_effect_source_status")
        or primary_weapon_log.get("weapon_effect_source_status"),
        concerto_energy_before_weapon_effect=float(
            echo_set_log_fields.get("concerto_energy_before_weapon_effect", 0.0) or 0.0
        ),
        concerto_energy_restored_by_weapon=float(
            echo_set_log_fields.get("concerto_energy_restored_by_weapon", 0.0) or 0.0
        ),
        concerto_energy_after_weapon_effect=float(
            echo_set_log_fields.get("concerto_energy_after_weapon_effect", 0.0) or 0.0
        ),
        concerto_energy_wasted_by_weapon=float(
            echo_set_log_fields.get("concerto_energy_wasted_by_weapon", 0.0) or 0.0
        ),
        weapon_effect_cooldown_seconds=float(echo_set_log_fields.get("weapon_effect_cooldown_seconds", 0.0) or 0.0),
        weapon_effect_cooldown_remaining=float(
            echo_set_log_fields.get("weapon_effect_cooldown_remaining", 0.0) or 0.0
        ),
        weapon_effect_cooldown_blocked=bool(echo_set_log_fields.get("weapon_effect_cooldown_blocked", False)),
        weapon_effect_buff_refreshed=bool(
            echo_set_log_fields.get("weapon_effect_buff_refreshed", primary_weapon_log.get("weapon_effect_buff_refreshed", False))
        ),
        weapon_effect_duration_seconds=float(
            echo_set_log_fields.get(
                "weapon_effect_duration_seconds",
                primary_weapon_log.get("weapon_effect_duration_seconds", 0.0),
            )
            or 0.0
        ),
        aemeath_trailblazing_star_5set_active=AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in active_buff_ids,
        high_syntony_field_active=bool(
            action_damage_bonus_context.get(
                "high_syntony_field_active",
                echo_set_log_fields.get("high_syntony_field_active", False),
            )
        ),
        high_syntony_field_remaining=float(echo_set_log_fields.get("high_syntony_field_remaining", 0.0) or 0.0),
        high_syntony_field_created_count=int(echo_set_log_fields.get("high_syntony_field_created_count", 0) or 0),
        high_syntony_field_def_bonus_active=bool(
            action_damage_bonus_context.get(
                "high_syntony_field_def_bonus_active",
                echo_set_log_fields.get("high_syntony_field_def_bonus_active", False),
            )
        ),
        high_syntony_field_def_percent_bonus=float(
            action_damage_bonus_context.get(
                "high_syntony_field_def_percent_bonus",
                echo_set_log_fields.get("high_syntony_field_def_percent_bonus", 0.0),
            )
            or 0.0
        ),
        high_syntony_field_off_tune_inherited=bool(
            action_damage_bonus_context.get(
                "high_syntony_field_off_tune_inherited",
                echo_set_log_fields.get("high_syntony_field_off_tune_inherited", False),
            )
        ),
        high_syntony_field_heal_proxy_active=bool(echo_set_log_fields.get("high_syntony_field_heal_proxy_active", False)),
        high_syntony_field_healing_multiplier_bonus=float(
            echo_set_log_fields.get("high_syntony_field_healing_multiplier_bonus", 0.0) or 0.0
        ),
        high_syntony_field_healing_multiplier_metadata_only=bool(
            echo_set_log_fields.get("high_syntony_field_healing_multiplier_metadata_only", True)
        ),
        critical_protocol_high_syntony_created_before_damage=bool(
            echo_set_log_fields.get("critical_protocol_high_syntony_created_before_damage", False)
        ),
        high_syntony_field_same_action_application=bool(
            echo_set_log_fields.get("high_syntony_field_same_action_application", False)
        ),
        high_syntony_field_application_timing=echo_set_log_fields.get("high_syntony_field_application_timing"),
        high_syntony_field_unavailable_reason=echo_set_log_fields.get("high_syntony_field_unavailable_reason"),
        halo_atk_buff_does_not_affect_mornye_def_damage=bool(
            action_damage_bonus_context.get(
                "halo_atk_buff_does_not_affect_mornye_def_damage",
                echo_set_log_fields.get("halo_atk_buff_does_not_affect_mornye_def_damage", False),
            )
        ),
        halo_of_starry_radiance_5set_active=bool(
            action_damage_bonus_context.get(
                "halo_of_starry_radiance_5set_active",
                MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID in active_buff_ids,
            )
        ),
        halo_of_starry_radiance_5set_atk_percent_bonus=float(
            action_damage_bonus_context.get("halo_of_starry_radiance_5set_atk_percent_bonus", 0.0) or 0.0
        ),
        active_anomalies_after=active_anomalies_after,
        active_buffs=active_buff_ids,
        applied_buffs=applied_buff_ids,
        valid=True,
        base_resonance_energy_gain=resource_change.base_resonance_energy_gain if resource_change is not None else 0.0,
        energy_regen=resource_change.energy_regen if resource_change is not None else 1.0,
        final_resonance_energy_gain=resource_change.final_resonance_energy_gain if resource_change is not None else 0.0,
        resonance_energy_gained=resource_change.resonance_gained if resource_change is not None else 0.0,
        resonance_energy_wasted=resource_change.resonance_wasted if resource_change is not None else 0.0,
        concerto_before=resource_change.concerto_before if resource_change is not None else 0.0,
        concerto_gain=resource_change.concerto_gained if resource_change is not None else 0.0,
        concerto_after=resource_change.concerto_after if resource_change is not None else 0.0,
        concerto_ready_after=resource_change.concerto_ready_after if resource_change is not None else False,
        concerto_energy_gained=resource_change.concerto_gained if resource_change is not None else 0.0,
        concerto_energy_wasted=resource_change.concerto_wasted if resource_change is not None else 0.0,
        **mechanic_log_fields,
    )
    state.action_log.append(result.model_dump(mode="json"))
    if total_action_damage > 0.0 or damage_after_cutoff_excluded > 0.0:
        state.damage_log.append(
            {
                "action_id": action.id,
                "actor_character_id": actor_character_id,
                "damage_before_cutoff": total_action_damage,
                "damage_after_cutoff_excluded": damage_after_cutoff_excluded,
                "generated_mechanic_damage": generated_mechanic_damage,
                "generated_mechanic_damage_events": generated_mechanic_events,
                "scheduled_damage": scheduled_damage,
                "scheduled_damage_events": scheduled_damage_events,
                "scheduled_healing_events": scheduled_healing_events,
                "scheduled_status_application_events": scheduled_status_application_events,
                **action_damage_bonus_context,
                **mechanic_event_log_fields,
                **echo_set_log_fields,
                "aemeath_trailblazing_star_5set_active": AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in active_buff_ids,
                "halo_of_starry_radiance_5set_active": bool(
                    action_damage_bonus_context.get(
                        "halo_of_starry_radiance_5set_active",
                        MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID in active_buff_ids,
                    )
                ),
                "active_buff_ids": active_buff_ids,
                "combat_time_start": combat_start_time,
                "combat_time_end": state.combat_time,
            }
        )
    return result


def execute_scheduled_damage_event(
    *,
    effect: ScheduledEffectState,
    payload_action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    host_action_id: str,
    combat_time: float,
    host_action_combat_offset: float,
    trigger_index: int,
    action_start_snapshot: ActionStartEffectSnapshot | None = None,
    force_active_buff_ids: set[str] | None = None,
    weapon_definitions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if effect.source_character_id not in characters:
        raise ValueError(f"Scheduled effect source character {effect.source_character_id!r} is unavailable")
    action = payload_action.model_copy(update={"character_id": effect.source_character_id})
    action_time = action.effective_action_time
    (
        normal_damage,
        tune_break_damage,
        hit_details,
        hit_damage_by_category,
        _damage_after_cutoff_excluded,
        action_damage_bonus_context,
        direct_amp_summary,
    ) = _calculate_hit_damage_totals(
        action,
        state,
        characters,
        buffs,
        action_time=action_time,
        combat_time_cost=0.0,
        combat_start_time=combat_time,
        combat_duration=None,
        truncated_by_combat_limit=False,
        force_active_buff_ids=force_active_buff_ids,
        action_start_snapshot=action_start_snapshot,
        weapon_definitions=weapon_definitions,
    )
    damage = normal_damage + tune_break_damage
    event = {
        "event_type": "scheduled_damage",
        "scheduled_effect_instance_id": effect.instance_id,
        "scheduled_effect_id": effect.effect_id,
        "source_character_id": effect.source_character_id,
        "source_action_id": effect.source_action_id,
        "payload_action_id": action.id,
        "payload_action_name": action.name,
        "host_action_id": host_action_id,
        "trigger_index": trigger_index,
        "combat_time": combat_time,
        "host_action_combat_offset": host_action_combat_offset,
        "damage": damage,
        "normal_damage": normal_damage,
        "tune_break_damage": tune_break_damage,
        "hit_details": hit_details,
        "hit_damage_by_category": hit_damage_by_category,
        "source_status": effect.source_status,
        "source_ref": effect.source_ref,
        "metadata": dict(effect.metadata or {}),
        "direct_damage_taken_amp_total_bonus_damage": float(
            direct_amp_summary.get("direct_damage_taken_amp_total_bonus_damage", 0.0) or 0.0
        ),
        "interfered_marker_direct_damage_amp_applied_count": int(
            direct_amp_summary.get("interfered_marker_direct_damage_amp_applied_count", 0) or 0
        ),
        "interfered_marker_direct_damage_amp_bonus_damage": float(
            direct_amp_summary.get("interfered_marker_direct_damage_amp_bonus_damage", 0.0) or 0.0
        ),
        **action_damage_bonus_context,
    }
    state.scheduled_effect_event_log.append(event)
    if damage > 0.0:
        state.damage_log.append(
            {
                "event_type": "scheduled_damage",
                "action_id": action.id,
                "actor_character_id": effect.source_character_id,
                "scheduled_effect_instance_id": effect.instance_id,
                "scheduled_effect_id": effect.effect_id,
                "host_action_id": host_action_id,
                "damage_before_cutoff": damage,
                "damage_after_cutoff_excluded": 0.0,
                "combat_time_start": combat_time,
                "combat_time_end": combat_time,
                **action_damage_bonus_context,
            }
        )
    return event


def timeline_entry(result: ActionResult, active_character_name: str) -> TimelineEntry:
    return TimelineEntry(
        selected_action_id=result.selected_action_id,
        selected_action_name=result.selected_action_name,
        resolved_action_id=result.resolved_action_id or result.action_id,
        resolved_action_name=result.resolved_action_name or result.action_name,
        time_start=result.start_time,
        time_end=result.end_time,
        action_id=result.action_id,
        action_name=result.action_name,
        character_id=result.character_id,
        actor_character_id=result.actor_character_id,
        active_character_before=result.active_character_before,
        active_character_after=result.active_character_after,
        action_time=result.action_time,
        combat_time_start=result.combat_time_start,
        combat_time_end=result.combat_time_end,
        combat_time_cost=result.combat_time_cost,
        effective_combat_time_cost=result.effective_combat_time_cost,
        combat_time_cost_source=result.combat_time_cost_source,
        has_global_time_stop=result.has_global_time_stop,
        global_time_stop_frames=result.global_time_stop_frames,
        source_sheet=result.source_sheet,
        source_rows=result.source_rows,
        truncated_by_combat_limit=result.truncated_by_combat_limit,
        damage_before_cutoff=result.damage_before_cutoff,
        damage_after_cutoff_excluded=result.damage_after_cutoff_excluded,
        damage=result.damage,
        normal_damage=result.normal_damage,
        tune_break_damage=result.tune_break_damage,
        direct_action_damage=result.direct_action_damage,
        scheduled_damage=result.scheduled_damage,
        scheduled_damage_events=result.scheduled_damage_events,
        scheduled_healing_events=result.scheduled_healing_events,
        scheduled_status_application_events=result.scheduled_status_application_events,
        direct_damage_taken_amp_total_bonus_damage=result.direct_damage_taken_amp_total_bonus_damage,
        interfered_marker_direct_damage_amp_applied_count=result.interfered_marker_direct_damage_amp_applied_count,
        interfered_marker_direct_damage_amp_bonus_damage=result.interfered_marker_direct_damage_amp_bonus_damage,
        interfered_marker_direct_damage_amp_source_ref=result.interfered_marker_direct_damage_amp_source_ref,
        tune_break_damage_receives_existing_interfered_marker_amp=(
            result.tune_break_damage_receives_existing_interfered_marker_amp
        ),
        tune_break_damage_receives_newly_applied_interfered_marker_amp=(
            result.tune_break_damage_receives_newly_applied_interfered_marker_amp
        ),
        tune_break_damage_before_target_amp=result.tune_break_damage_before_target_amp,
        tune_break_damage_after_target_amp=result.tune_break_damage_after_target_amp,
        target_tune_strain_interfered_stacks=result.target_tune_strain_interfered_stacks,
        target_tune_strain_interfered_max_stacks=result.target_tune_strain_interfered_max_stacks,
        target_tune_strain_interfered_remaining=result.target_tune_strain_interfered_remaining,
        lynae_tune_strain_damage_amp=result.lynae_tune_strain_damage_amp,
        lynae_tune_strain_damage_multiplier=result.lynae_tune_strain_damage_multiplier,
        lynae_tune_strain_damage_amp_bonus_damage=result.lynae_tune_strain_damage_amp_bonus_damage,
        lynae_tune_strain_source_status=result.lynae_tune_strain_source_status,
        lynae_tune_strain_source_ref=result.lynae_tune_strain_source_ref,
        generated_mechanic_damage=result.generated_mechanic_damage,
        generated_mechanic_damage_total=result.generated_mechanic_damage_total,
        generated_mechanic_hit_count=result.generated_mechanic_hit_count,
        generated_mechanic_damage_events=result.generated_mechanic_damage_events,
        aemeath_forte_generated_damage=result.aemeath_forte_generated_damage,
        aemeath_forte_generated_damage_total=result.aemeath_forte_generated_damage_total,
        aemeath_seraphic_duet_followup_triggered=result.aemeath_seraphic_duet_followup_triggered,
        aemeath_seraphic_duet_followup_damage=result.aemeath_seraphic_duet_followup_damage,
        aemeath_seraphic_duet_followup_source_status=result.aemeath_seraphic_duet_followup_source_status,
        aemeath_seraphic_duet_followup_mode=result.aemeath_seraphic_duet_followup_mode,
        aemeath_seraphic_duet_followup_variant=result.aemeath_seraphic_duet_followup_variant,
        aemeath_seraphic_duet_followup_repeat_count=result.aemeath_seraphic_duet_followup_repeat_count,
        aemeath_seraphic_duet_followup_multiplier=result.aemeath_seraphic_duet_followup_multiplier,
        aemeath_seraphic_duet_trail_stack_snapshot=result.aemeath_seraphic_duet_trail_stack_snapshot,
        aemeath_seraphic_duet_trail_stack_factor=result.aemeath_seraphic_duet_trail_stack_factor,
        aemeath_seraphic_duet_trail_preservation_active=result.aemeath_seraphic_duet_trail_preservation_active,
        aemeath_seraphic_duet_trail_preservation_after=result.aemeath_seraphic_duet_trail_preservation_after,
        aemeath_seraphic_duet_trail_consumed=result.aemeath_seraphic_duet_trail_consumed,
        aemeath_seraphic_duet_total_extra_tune_multiplier=result.aemeath_seraphic_duet_total_extra_tune_multiplier,
        aemeath_rupturous_trail_stacks_before=result.aemeath_rupturous_trail_stacks_before,
        aemeath_rupturous_trail_stacks_consumed=result.aemeath_rupturous_trail_stacks_consumed,
        aemeath_rupturous_trail_stacks_after=result.aemeath_rupturous_trail_stacks_after,
        aemeath_rupturous_trail_gain_events=result.aemeath_rupturous_trail_gain_events,
        aemeath_forte_enhancement_stacks_before=result.aemeath_forte_enhancement_stacks_before,
        aemeath_forte_enhancement_stacks_consumed=result.aemeath_forte_enhancement_stacks_consumed,
        aemeath_forte_enhancement_stacks_after=result.aemeath_forte_enhancement_stacks_after,
        aemeath_trail_no_cost_consumed=result.aemeath_trail_no_cost_consumed,
        aemeath_stardust_resonance_active_for_followup=result.aemeath_stardust_resonance_active_for_followup,
        aemeath_seraphic_duet_followup_source_rows=result.aemeath_seraphic_duet_followup_source_rows,
        direct_anomaly_damage=result.direct_anomaly_damage,
        anomaly_tick_damage=result.anomaly_tick_damage,
        anomaly_damage=result.anomaly_damage,
        anomaly_damage_by_type=result.anomaly_damage_by_type,
        total_action_damage=result.total_action_damage,
        total_damage_after=result.total_damage_after,
        hit_count=result.hit_count,
        hit_damage_by_category=result.hit_damage_by_category,
        hit_details=result.hit_details,
        action_type=result.action_type,
        damage_category=result.damage_category,
        damage_bonus_category=result.damage_bonus_category,
        damage_element=result.damage_element,
        raw_skill_category=result.raw_skill_category,
        raw_damage_type=result.raw_damage_type,
        all_dmg_bonus=result.all_dmg_bonus,
        category_dmg_bonus=result.category_dmg_bonus,
        element_dmg_bonus=result.element_dmg_bonus,
        runtime_element_damage_bonus=result.runtime_element_damage_bonus,
        echo_set_damage_bonus=result.echo_set_damage_bonus,
        effective_damage_bonus=result.effective_damage_bonus,
        crit_rate_before_buffs=result.crit_rate_before_buffs,
        crit_rate_after_buffs=result.crit_rate_after_buffs,
        crit_damage_before_buffs=result.crit_damage_before_buffs,
        crit_damage_after_buffs=result.crit_damage_after_buffs,
        runtime_crit_damage_bonus=result.runtime_crit_damage_bonus,
        starfield_calibrator_party_crit_damage_active=result.starfield_calibrator_party_crit_damage_active,
        starfield_calibrator_party_crit_damage_bonus=result.starfield_calibrator_party_crit_damage_bonus,
        everbright_polestar_all_attribute_bonus_active=result.everbright_polestar_all_attribute_bonus_active,
        everbright_polestar_all_attribute_damage_bonus=result.everbright_polestar_all_attribute_damage_bonus,
        runtime_all_attribute_damage_bonus=result.runtime_all_attribute_damage_bonus,
        element_damage_bonus_before_weapon=result.element_damage_bonus_before_weapon,
        element_damage_bonus_after_weapon=result.element_damage_bonus_after_weapon,
        everbright_polestar_liberation_penetration_active=result.everbright_polestar_liberation_penetration_active,
        everbright_polestar_liberation_penetration_remaining=result.everbright_polestar_liberation_penetration_remaining,
        def_ignore_before_weapon=result.def_ignore_before_weapon,
        everbright_polestar_def_ignore_bonus=result.everbright_polestar_def_ignore_bonus,
        total_def_ignore=result.total_def_ignore,
        def_multiplier_before_weapon=result.def_multiplier_before_weapon,
        def_multiplier_after_weapon=result.def_multiplier_after_weapon,
        enemy_res_before_weapon=result.enemy_res_before_weapon,
        everbright_polestar_fusion_res_ignore_bonus=result.everbright_polestar_fusion_res_ignore_bonus,
        enemy_res_after_weapon=result.enemy_res_after_weapon,
        res_multiplier_before_weapon=result.res_multiplier_before_weapon,
        res_multiplier_after_weapon=result.res_multiplier_after_weapon,
        damage_element_fallback_used_for_weapon_res_ignore=result.damage_element_fallback_used_for_weapon_res_ignore,
        build_profile_id=result.build_profile_id,
        scaling_stat=result.scaling_stat,
        scaling_value=result.scaling_value,
        stat_component_source=result.stat_component_source,
        unresolved_scaling_actions=result.unresolved_scaling_actions,
        **stat_component_log_fields(result),
        profile_completeness_status=result.profile_completeness_status,
        implementation_status=result.implementation_status,
        emitted_mechanic_event_tags=result.emitted_mechanic_event_tags,
        mechanic_event_triggered=result.mechanic_event_triggered,
        mechanic_event_trigger_id=result.mechanic_event_trigger_id,
        mechanic_event_cooldown_blocked=result.mechanic_event_cooldown_blocked,
        aemeath_resonance_mode=result.aemeath_resonance_mode,
        mechanic_event_source_status=result.mechanic_event_source_status,
        mechanic_event_unresolved_reason=result.mechanic_event_unresolved_reason,
        echo_set_triggered_buff_ids=result.echo_set_triggered_buff_ids,
        echo_set_buff_refreshed=result.echo_set_buff_refreshed,
        weapon_effects_enabled=result.weapon_effects_enabled,
        weapon_effect_triggered=result.weapon_effect_triggered,
        weapon_effect_logs=result.weapon_effect_logs,
        weapon_effect_trigger_counts=result.weapon_effect_trigger_counts,
        weapon_effect_cooldown_blocked_counts=result.weapon_effect_cooldown_blocked_counts,
        weapon_id=result.weapon_id,
        weapon_rank=result.weapon_rank,
        weapon_effect_id=result.weapon_effect_id,
        weapon_effect_type=result.weapon_effect_type,
        weapon_effect_resource=result.weapon_effect_resource,
        weapon_effect_source_status=result.weapon_effect_source_status,
        concerto_energy_before_weapon_effect=result.concerto_energy_before_weapon_effect,
        concerto_energy_restored_by_weapon=result.concerto_energy_restored_by_weapon,
        concerto_energy_after_weapon_effect=result.concerto_energy_after_weapon_effect,
        concerto_energy_wasted_by_weapon=result.concerto_energy_wasted_by_weapon,
        weapon_effect_cooldown_seconds=result.weapon_effect_cooldown_seconds,
        weapon_effect_cooldown_remaining=result.weapon_effect_cooldown_remaining,
        weapon_effect_cooldown_blocked=result.weapon_effect_cooldown_blocked,
        weapon_effect_buff_refreshed=result.weapon_effect_buff_refreshed,
        weapon_effect_duration_seconds=result.weapon_effect_duration_seconds,
        starfield_calibrator_concerto_restore_trigger_count=result.starfield_calibrator_concerto_restore_trigger_count,
        starfield_calibrator_party_crit_damage_trigger_count=result.starfield_calibrator_party_crit_damage_trigger_count,
        aemeath_trailblazing_star_5set_active=result.aemeath_trailblazing_star_5set_active,
        aemeath_trailblazing_star_5set_applied_before_triggering_damage=(
            result.aemeath_trailblazing_star_5set_applied_before_triggering_damage
        ),
        trailblazing_star_5set_same_action_application=result.trailblazing_star_5set_same_action_application,
        trailblazing_star_5set_application_timing=result.trailblazing_star_5set_application_timing,
        base_off_tune_buildup_rate=result.base_off_tune_buildup_rate,
        runtime_off_tune_buildup_rate_bonus=result.runtime_off_tune_buildup_rate_bonus,
        current_off_tune_buildup_rate=result.current_off_tune_buildup_rate,
        base_tune_break_boost_points=result.base_tune_break_boost_points,
        runtime_tune_break_boost_points_bonus=result.runtime_tune_break_boost_points_bonus,
        current_tune_break_boost_points=result.current_tune_break_boost_points,
        syntony_field_off_tune_bonus_active=result.syntony_field_off_tune_bonus_active,
        syntony_field_off_tune_bonus_value=result.syntony_field_off_tune_bonus_value,
        c2_off_tune_bonus_active=result.c2_off_tune_bonus_active,
        mornye_constellation=result.mornye_constellation,
        mornye_heal_event_mode=result.mornye_heal_event_mode,
        team_heal_event_triggered=result.team_heal_event_triggered,
        halo_of_starry_radiance_5set_active=result.halo_of_starry_radiance_5set_active,
        halo_of_starry_radiance_5set_atk_percent_bonus=result.halo_of_starry_radiance_5set_atk_percent_bonus,
        halo_of_starry_radiance_5set_applied_before_field_creation_damage=(
            result.halo_of_starry_radiance_5set_applied_before_field_creation_damage
        ),
        halo_of_starry_radiance_5set_same_action_application=result.halo_of_starry_radiance_5set_same_action_application,
        halo_of_starry_radiance_5set_application_timing=result.halo_of_starry_radiance_5set_application_timing,
        halo_of_starry_radiance_5set_unavailable_reason=result.halo_of_starry_radiance_5set_unavailable_reason,
        pact_neonlight_incoming_atk_buff=result.pact_neonlight_incoming_atk_buff,
        pact_neonlight_incoming_atk_base=result.pact_neonlight_incoming_atk_base,
        pact_neonlight_incoming_atk_from_tune_break_boost=result.pact_neonlight_incoming_atk_from_tune_break_boost,
        pact_neonlight_incoming_atk_total=result.pact_neonlight_incoming_atk_total,
        pact_neonlight_source_status=result.pact_neonlight_source_status,
        lynae_static_mist_incoming_atk_buff=result.lynae_static_mist_incoming_atk_buff,
        lynae_static_mist_incoming_atk_value=result.lynae_static_mist_incoming_atk_value,
        lynae_hyvatia_incoming_all_attribute_buff=result.lynae_hyvatia_incoming_all_attribute_buff,
        lynae_hyvatia_incoming_all_attribute_value=result.lynae_hyvatia_incoming_all_attribute_value,
        lynae_outro_all_damage_amp_value=result.lynae_outro_all_damage_amp_value,
        lynae_outro_liberation_damage_amp_value=result.lynae_outro_liberation_damage_amp_value,
        lynae_liberation_party_damage_buff_active=result.lynae_liberation_party_damage_buff_active,
        lynae_liberation_party_damage_buff_value=result.lynae_liberation_party_damage_buff_value,
        lynae_overflow=result.lynae_overflow,
        lynae_overflow_max=result.lynae_overflow_max,
        lynae_lumiflow=result.lynae_lumiflow,
        lynae_true_color=result.lynae_true_color,
        lynae_kaleidoscopic_parade_remaining=result.lynae_kaleidoscopic_parade_remaining,
        lynae_optical_sampling_stage_active=result.lynae_optical_sampling_stage_active,
        lynae_resonance_mode=result.lynae_resonance_mode,
        lynae_photocromic_flux_active=result.lynae_photocromic_flux_active,
        lynae_photocromic_flux_applied=result.lynae_photocromic_flux_applied,
        lynae_photocromic_flux_remaining=result.lynae_photocromic_flux_remaining,
        lynae_photocromic_flux_mode=result.lynae_photocromic_flux_mode,
        lynae_photocromic_flux_source_status=result.lynae_photocromic_flux_source_status,
        lynae_photocromic_flux_unresolved_reason=result.lynae_photocromic_flux_unresolved_reason,
        lynae_target_tune_shift_state=result.lynae_target_tune_shift_state,
        lynae_target_tune_shift_remaining=result.lynae_target_tune_shift_remaining,
        lynae_spray_paint_window_remaining=result.lynae_spray_paint_window_remaining,
        lynae_spray_paint_scheduled=result.lynae_spray_paint_scheduled,
        lynae_spray_paint_schedule_operation=result.lynae_spray_paint_schedule_operation,
        lynae_spray_paint_mode_snapshot=result.lynae_spray_paint_mode_snapshot,
        lynae_spray_paint_target_shift_state_snapshot=result.lynae_spray_paint_target_shift_state_snapshot,
        lynae_spray_paint_source_ref=result.lynae_spray_paint_source_ref,
        lynae_visual_impact_cooldown_remaining=result.lynae_visual_impact_cooldown_remaining,
        lynae_visual_impact_tune_break_boost_buff_active=result.lynae_visual_impact_tune_break_boost_buff_active,
        lynae_visual_impact_tune_break_boost_value=result.lynae_visual_impact_tune_break_boost_value,
        lynae_to_vivid_tomorrow_window_remaining=result.lynae_to_vivid_tomorrow_window_remaining,
        active_anomalies_after=result.active_anomalies_after,
        active_buffs=result.active_buffs,
        applied_buffs=result.applied_buffs,
        outgoing_character_id=result.outgoing_character_id,
        incoming_character_id=result.incoming_character_id,
        transition_type=result.transition_type,
        transition_reason=result.transition_reason,
        outgoing_concerto_before=result.outgoing_concerto_before,
        outgoing_concerto_ready=result.outgoing_concerto_ready,
        outgoing_concerto_consumed=result.outgoing_concerto_consumed,
        outgoing_concerto_after=result.outgoing_concerto_after,
        incoming_qte_candidate_id=result.incoming_qte_candidate_id,
        incoming_qte_mode=result.incoming_qte_mode,
        incoming_qte_applied=result.incoming_qte_applied,
        incoming_qte_damage_bonus_category=result.incoming_qte_damage_bonus_category,
        incoming_qte_trigger_classification=result.incoming_qte_trigger_classification,
        incoming_qte_source_damage_label=result.incoming_qte_source_damage_label,
        incoming_qte_previous_outro_trigger_frame=result.incoming_qte_previous_outro_trigger_frame,
        incoming_qte_flow_light_metadata_present=result.incoming_qte_flow_light_metadata_present,
        incoming_qte_flow_light_applied=result.incoming_qte_flow_light_applied,
        incoming_intro_candidate_id=result.incoming_intro_candidate_id,
        incoming_intro_mode=result.incoming_intro_mode,
        incoming_intro_applied=result.incoming_intro_applied,
        incoming_intro_damage_bonus_category=result.incoming_intro_damage_bonus_category,
        incoming_intro_trigger_classification=result.incoming_intro_trigger_classification,
        incoming_intro_source_damage_label=result.incoming_intro_source_damage_label,
        outgoing_outro_applied=result.outgoing_outro_applied,
        transition_events=result.transition_events,
        transition_event_details=result.transition_event_details,
        outgoing_outro_event_id=result.outgoing_outro_event_id,
        incoming_intro_event_id=result.incoming_intro_event_id,
        fallback_swap_used=result.fallback_swap_used,
        swap_timing_is_placeholder=result.swap_timing_is_placeholder,
        swap_timing_source=result.swap_timing_source,
        transition_warnings=result.transition_warnings,
        active_character=active_character_name,
        base_resonance_energy_gain=result.base_resonance_energy_gain,
        energy_regen=result.energy_regen,
        final_resonance_energy_gain=result.final_resonance_energy_gain,
        resonance_energy_gained=result.resonance_energy_gained,
        resonance_energy_wasted=result.resonance_energy_wasted,
        concerto_before=result.concerto_before,
        concerto_gain=result.concerto_gain,
        concerto_after=result.concerto_after,
        concerto_ready_after=result.concerto_ready_after,
        concerto_energy_gained=result.concerto_energy_gained,
        concerto_energy_wasted=result.concerto_energy_wasted,
        base_concerto_gain=result.base_concerto_gain,
        passive_concerto_gain=result.passive_concerto_gain,
        final_concerto_gain=result.final_concerto_gain,
        passive_concerto_source=result.passive_concerto_source,
        relative_momentum_gain=result.relative_momentum_gain,
        relative_momentum_gain_source_rows=result.relative_momentum_gain_source_rows,
        distributed_array_base_concerto_gain=result.distributed_array_base_concerto_gain,
        distributed_array_relative_momentum_gain_per_hit=result.distributed_array_relative_momentum_gain_per_hit,
        distributed_array_relative_momentum_gain_total=result.distributed_array_relative_momentum_gain_total,
        time_dilation_type=result.time_dilation_type,
        source_status=result.source_status,
        mechanic_debug_after=result.mechanic_debug_after,
        mornye_mode_after=result.mornye_mode_after,
        mornye_rest_mass_after=result.mornye_rest_mass_after,
        mornye_wfo_remaining_after=result.mornye_wfo_remaining_after,
        mornye_syntony_field_remaining_after=result.mornye_syntony_field_remaining_after,
        high_syntony_field_active=result.high_syntony_field_active,
        high_syntony_field_remaining=result.high_syntony_field_remaining,
        high_syntony_field_created_count=result.high_syntony_field_created_count,
        high_syntony_field_def_bonus_active=result.high_syntony_field_def_bonus_active,
        high_syntony_field_def_percent_bonus=result.high_syntony_field_def_percent_bonus,
        high_syntony_field_off_tune_inherited=result.high_syntony_field_off_tune_inherited,
        high_syntony_field_heal_proxy_active=result.high_syntony_field_heal_proxy_active,
        high_syntony_field_healing_multiplier_bonus=result.high_syntony_field_healing_multiplier_bonus,
        high_syntony_field_healing_multiplier_metadata_only=result.high_syntony_field_healing_multiplier_metadata_only,
        critical_protocol_high_syntony_created_before_damage=result.critical_protocol_high_syntony_created_before_damage,
        high_syntony_field_same_action_application=result.high_syntony_field_same_action_application,
        high_syntony_field_application_timing=result.high_syntony_field_application_timing,
        high_syntony_field_unavailable_reason=result.high_syntony_field_unavailable_reason,
        off_tune_value=result.off_tune_value,
        off_tune_value_source_status=result.off_tune_value_source_status,
        off_tune_value_source_ref=result.off_tune_value_source_ref,
        off_tune_buildup_rate_used=result.off_tune_buildup_rate_used,
        off_tune_added=result.off_tune_added,
        enemy_off_tune_current_before=result.enemy_off_tune_current_before,
        enemy_off_tune_current_after=result.enemy_off_tune_current_after,
        off_tune_accumulation_blocked_by_tune_break_cooldown=(
            result.off_tune_accumulation_blocked_by_tune_break_cooldown
        ),
        off_tune_value_before_block=result.off_tune_value_before_block,
        enemy_off_tune_max=result.enemy_off_tune_max,
        enemy_mistune_active=result.enemy_mistune_active,
        enemy_tune_break_available=result.enemy_tune_break_available,
        enemy_off_tune_current_after_tune_break=result.enemy_off_tune_current_after_tune_break,
        enemy_tune_break_cooldown_started=result.enemy_tune_break_cooldown_started,
        enemy_tune_break_cooldown_seconds=result.enemy_tune_break_cooldown_seconds,
        enemy_tune_break_cooldown_source_status=result.enemy_tune_break_cooldown_source_status,
        enemy_tune_break_cooldown_source_ref=result.enemy_tune_break_cooldown_source_ref,
        enemy_tune_break_cooldown_remaining=result.enemy_tune_break_cooldown_remaining,
        enemy_mistune_entered_this_action=result.enemy_mistune_entered_this_action,
        off_tune_accumulation_log=result.off_tune_accumulation_log,
        tune_break_action_available_ids=result.tune_break_action_available_ids,
        tune_break_action_used_count=result.tune_break_action_used_count,
        tune_break_damage_total=result.tune_break_damage_total,
        target_tune_shift_state=result.target_tune_shift_state,
        target_tune_shift_remaining=result.target_tune_shift_remaining,
        target_interfered_state=result.target_interfered_state,
        target_interfered_remaining=result.target_interfered_remaining,
        interfered_unavailable_reason=result.interfered_unavailable_reason,
        observation_marker_active=result.observation_marker_active,
        observation_marker_remaining=result.observation_marker_remaining,
        interfered_marker_active=result.interfered_marker_active,
        interfered_marker_remaining=result.interfered_marker_remaining,
        interfered_marker_applied_count=result.interfered_marker_applied_count,
        interfered_marker_damage_taken_amp=result.interfered_marker_damage_taken_amp,
        interfered_marker_damage_taken_multiplier=result.interfered_marker_damage_taken_multiplier,
        mornye_energy_regen_for_interfered_marker=result.mornye_energy_regen_for_interfered_marker,
        energy_regen_excess_for_interfered_marker=result.energy_regen_excess_for_interfered_marker,
        interfered_marker_cap_applied=result.interfered_marker_cap_applied,
        interfered_marker_source=result.interfered_marker_source,
        interfered_marker_newly_applied_this_action=result.interfered_marker_newly_applied_this_action,
        previous_interfered_marker_active_before_response=result.previous_interfered_marker_active_before_response,
        party_response_scan_triggered=result.party_response_scan_triggered,
        tune_break_response_event_tags=result.tune_break_response_event_tags,
        aemeath_starburst_triggered=result.aemeath_starburst_triggered,
        aemeath_starburst_cooldown_blocked=result.aemeath_starburst_cooldown_blocked,
        aemeath_starburst_cooldown_started=result.aemeath_starburst_cooldown_started,
        aemeath_starburst_response_cooldown_remaining=result.aemeath_starburst_response_cooldown_remaining,
        aemeath_starburst_response_damage=result.aemeath_starburst_response_damage,
        aemeath_starburst_damage_total=result.aemeath_starburst_damage_total,
        aemeath_starburst_cooldown_blocked_count=result.aemeath_starburst_cooldown_blocked_count,
        aemeath_starburst_damage_unresolved=result.aemeath_starburst_damage_unresolved,
        mornye_particle_jet_triggered=result.mornye_particle_jet_triggered,
        mornye_particle_jet_cooldown_blocked=result.mornye_particle_jet_cooldown_blocked,
        mornye_particle_jet_cooldown_started=result.mornye_particle_jet_cooldown_started,
        mornye_particle_jet_response_cooldown_remaining=result.mornye_particle_jet_response_cooldown_remaining,
        mornye_particle_jet_response_damage=result.mornye_particle_jet_response_damage,
        mornye_particle_jet_damage_total=result.mornye_particle_jet_damage_total,
        mornye_particle_jet_cooldown_blocked_count=result.mornye_particle_jet_cooldown_blocked_count,
        mornye_particle_jet_multiplier_used=result.mornye_particle_jet_multiplier_used,
        mornye_particle_jet_constellation_variant=result.mornye_particle_jet_constellation_variant,
        mornye_particle_jet_damage_unresolved=result.mornye_particle_jet_damage_unresolved,
        lynae_spectral_analysis_triggered=result.lynae_spectral_analysis_triggered,
        lynae_spectral_analysis_cooldown_blocked=result.lynae_spectral_analysis_cooldown_blocked,
        lynae_spectral_analysis_cooldown_started=result.lynae_spectral_analysis_cooldown_started,
        lynae_spectral_analysis_response_cooldown_remaining=result.lynae_spectral_analysis_response_cooldown_remaining,
        lynae_spectral_analysis_response_damage=result.lynae_spectral_analysis_response_damage,
        lynae_spectral_analysis_damage_total=result.lynae_spectral_analysis_damage_total,
        lynae_spectral_analysis_cooldown_blocked_count=result.lynae_spectral_analysis_cooldown_blocked_count,
        lynae_spectral_analysis_multiplier_used=result.lynae_spectral_analysis_multiplier_used,
        lynae_spectral_analysis_constellation_variant=result.lynae_spectral_analysis_constellation_variant,
        lynae_spectral_analysis_c2_disabled_by_default=result.lynae_spectral_analysis_c2_disabled_by_default,
        response_source_status=result.response_source_status,
        tune_response_damage=result.tune_response_damage,
        tune_response_damage_total=result.tune_response_damage_total,
        tune_response_hit_details=result.tune_response_hit_details,
        tune_response_events=result.tune_response_events,
        tune_response_damage_formula_source_status=result.tune_response_damage_formula_source_status,
        tune_response_event_order_source_status=result.tune_response_event_order_source_status,
        tune_break_damage_receives_new_interfered_marker_amp=result.tune_break_damage_receives_new_interfered_marker_amp,
        response_damage_receives_interfered_marker_amp=result.response_damage_receives_interfered_marker_amp,
        response_damage_receives_newly_applied_interfered_marker_amp=(
            result.response_damage_receives_newly_applied_interfered_marker_amp
        ),
        response_damage_receives_existing_interfered_marker_amp=(
            result.response_damage_receives_existing_interfered_marker_amp
        ),
        response_damage_receives_new_interfered_marker_amp=result.response_damage_receives_new_interfered_marker_amp,
        unresolved_response_damage_events=result.unresolved_response_damage_events,
        halo_atk_buff_does_not_affect_mornye_def_damage=result.halo_atk_buff_does_not_affect_mornye_def_damage,
        mornye_er_excess_percent=result.mornye_er_excess_percent,
        mornye_liberation_crit_rate_bonus=result.mornye_liberation_crit_rate_bonus,
        mornye_liberation_crit_dmg_bonus=result.mornye_liberation_crit_dmg_bonus,
        mornye_interfered_marker_mode=result.mornye_interfered_marker_mode,
        mornye_interfered_amp=result.mornye_interfered_amp,
        mornye_interfered_marker_applied=result.mornye_interfered_marker_applied,
        observation_marker_applied=result.observation_marker_applied,
        interfered_marker_mode=result.interfered_marker_mode,
        interfered_marker_applied_by_simplified_inversion=result.interfered_marker_applied_by_simplified_inversion,
        mornye_expectation_error_mode=result.mornye_expectation_error_mode,
        base_policy_action_id=result.base_policy_action_id,
        optimal_solution_triggered=result.optimal_solution_triggered,
        optimal_solution_trigger_reason=result.optimal_solution_trigger_reason,
        optimal_solution_candidate_id=result.optimal_solution_candidate_id,
        gp_success_modeled=result.gp_success_modeled,
    )
