from __future__ import annotations

from typing import Any

from simulator.anomaly_system import advance_anomalies, apply_anomaly, get_havoc_bane_def_reduction_at_time
from simulator.buff_system import (
    apply_buff,
    apply_buff_modifiers_to_damage_context,
    _recalculate_attack_stats,
    buffed_combat_stats,
    damage_amp_for_action,
    has_required_buffs,
    tick_buffs,
)
from simulator.build_profiles import damage_bonus_breakdown, scaling_value_for_action, stat_component_log_fields
from simulator.damage_formula import calculate_normal_damage, calculate_tune_break_damage
from simulator.echo_sets import AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID, apply_echo_set_event_buffs
from simulator.mechanic_events import preview_mechanic_event_trigger, process_mechanic_event_triggers
from simulator.models import ActionData, ActionResult, BuffData, CharacterData, CombatState, HitData, TimelineEntry
from simulator.resource_system import apply_resource_changes, can_pay_resources


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


def reduce_cooldowns(state: CombatState, elapsed: float) -> None:
    for action_id, remaining in list(state.cooldowns.items()):
        updated = max(0.0, remaining - elapsed)
        if updated > 0.0:
            state.cooldowns[action_id] = updated
        else:
            del state.cooldowns[action_id]


def resolve_action_timing(action: ActionData, actor_state: Any | None = None) -> tuple[float, float]:
    action_time = action.effective_action_time
    combat_time_cost = action.effective_combat_time_cost
    overrides = action.timing_overrides or {}

    instant_response = False
    if isinstance(actor_state, dict):
        instant_response = bool(actor_state.get("instant_response"))
    elif actor_state is not None:
        instant_response = bool(getattr(actor_state, "instant_response", False))

    if instant_response and "instant_response" in overrides:
        override = overrides["instant_response"]
        action_time = override.get("action_time", action_time)
        combat_time_cost = override.get("combat_time_cost", action_time)

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


def _calculate_hit_damage(
    hit: HitData,
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    temporary_stat_modifiers: dict[str, float] | None = None,
) -> tuple[float, dict]:
    transition_damage_action = bool((action.mechanic_effects or {}).get("transition_action"))
    if action.character_id is None or (action.action_type == "swap" and not transition_damage_action):
        return 0.0, {}

    character = characters[action.character_id]
    stats = buffed_combat_stats(character, state, buffs, time_offset=hit.time)
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
    damage_amp = damage_amp_for_action(action.character_id, action, state, buffs, time_offset=hit.time)
    damage_bonus_context = damage_bonus_breakdown(
        character,
        action,
        additive_buff_bonus=float(stats.get("damage_bonus_buff", 0.0)),
        additive_element_bonuses=stats.get("damage_bonus_by_element_buff") or {},
        echo_set_element_bonuses=stats.get("echo_set_damage_bonus_by_element") or {},
    )
    havoc_def_reduction = get_havoc_bane_def_reduction_at_time(state, hit.time)
    final_def_reduction = state.def_reduction + havoc_def_reduction
    scaling_stat, scaling_value = scaling_value_for_action(stats, action, character)

    damage = 0.0
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
        damage = calculate_tune_break_damage(
            tune_break_multiplier=hit.tune_break_multiplier,
            tune_break_boost_points=action.tune_break_boost_points,
            tune_dmg_bonus=state.tune_dmg_bonus,
            enemy_res=state.enemy_res,
            res_pen=state.res_pen,
            attacker_level=int(stats["attacker_level"]),
            enemy_level=state.enemy_level,
            def_ignore=stats["def_ignore"],
            def_reduction=final_def_reduction,
        )
    if damage > 0.0 and damage_amp != 0.0:
        damage = apply_buff_modifiers_to_damage_context(damage, damage_amp)

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
        "profile_completeness_status": character.profile_completeness_status,
        "implementation_status": character.implementation_status,
        "applied_havoc_bane_def_reduction": havoc_def_reduction,
        "applied_buff_summary": stats.get("active_buff_summary", []),
        "active_buff_ids": stats.get("active_buff_summary", []),
        "aemeath_trailblazing_star_5set_active": (
            AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in stats.get("active_buff_summary", [])
        ),
        "aemeath_trailblazing_star_5set_applied_before_triggering_damage": False,
        "trailblazing_star_5set_same_action_application": False,
        "trailblazing_star_5set_application_timing": None,
        "crit_rate_before_buffs": float(stats.get("crit_rate_before_buffs", character.crit_rate)),
        "crit_rate_after_buffs": float(stats.get("crit_rate_after_buffs", stats.get("crit_rate", 0.0))),
        "applied_damage_amp": damage_amp,
        "name": hit.name,
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
) -> tuple[float, float, list[dict], dict[str, float], float, dict[str, Any]]:
    normal_damage = 0.0
    tune_break_damage = 0.0
    damage_after_cutoff_excluded = 0.0
    hit_details: list[dict] = []
    damage_by_category: dict[str, float] = {}
    action_damage_bonus_context: dict[str, Any] = {}
    has_explicit_hit_timing = bool(action.hits)

    for hit in sorted(action.effective_hits(), key=lambda item: item.time):
        if hit.time > action_time:
            continue
        damage, detail = _calculate_hit_damage(hit, action, state, characters, buffs, temporary_stat_modifiers)
        if damage > 0.0 and action_damage_multiplier != 1.0:
            damage *= action_damage_multiplier
            detail["damage"] = damage
            detail["mechanic_damage_multiplier"] = action_damage_multiplier
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
                        "build_profile_id",
                        "scaling_stat",
                        "scaling_value",
                        "stat_component_source",
                        "profile_completeness_status",
                        "implementation_status",
                        *stat_component_log_fields(detail).keys(),
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

    return (
        normal_damage,
        tune_break_damage,
        hit_details,
        damage_by_category,
        damage_after_cutoff_excluded,
        action_damage_bonus_context,
    )


def _action_has_trigger_damage_potential(action: ActionData, action_time: float) -> bool:
    if action.character_id is None:
        return False
    for hit in action.effective_hits():
        if hit.time > action_time:
            continue
        if hit.damage_category == "normal" and hit.damage_multiplier > 0.0:
            return True
        if hit.damage_category == "tune_break" and hit.tune_break_multiplier > 0.0:
            return True
    return False


def execute_action(
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    mechanic: Any | None = None,
    combat_duration: float | None = None,
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
    action_time, combat_time_cost = resolve_action_timing(action, actor_state)
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

    echo_set_log_fields = {
        "echo_set_triggered_buff_ids": [],
        "echo_set_buff_refreshed": False,
        "aemeath_trailblazing_star_5set_applied_before_triggering_damage": False,
        "trailblazing_star_5set_same_action_application": False,
        "trailblazing_star_5set_application_timing": None,
    }
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
        echo_set_log_fields = apply_echo_set_event_buffs(
            actor_character_id=actor_character_id,
            emitted_event_tags=pre_damage_event_preview.get("emitted_mechanic_event_tags", []),
            characters=characters,
            state=state,
            buffs=buffs,
            application_time=start_time,
            applied_before_triggering_damage=True,
        )

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
    )
    direct_damage = normal_damage + tune_break_damage
    mechanic_event_log_fields = process_mechanic_event_triggers(
        action,
        state,
        direct_damage=direct_damage,
        action_start_combat_time=combat_start_time,
    )

    if action.action_type == "swap" and action.character_id is not None:
        state.active_character_id = action.character_id

    state.total_damage += direct_damage
    resource_change = None if truncated_by_combat_limit else apply_resource_changes(state, action, characters)

    state.current_time += action_time
    state.combat_time = combat_time_end
    reduce_cooldowns(state, effective_combat_time_cost)
    tick_buffs(state, action_time)
    anomaly_tick_damage, anomaly_damage_by_type = advance_anomalies(state, action_time)
    if truncated_by_combat_limit:
        damage_after_cutoff_excluded += anomaly_tick_damage
        anomaly_tick_damage = 0.0
        anomaly_damage_by_type = {}
    state.total_damage += anomaly_tick_damage

    total_action_damage = direct_damage + anomaly_tick_damage

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
        build_profile_id=action_damage_bonus_context.get("build_profile_id"),
        scaling_stat=action_damage_bonus_context.get("scaling_stat"),
        scaling_value=float(action_damage_bonus_context.get("scaling_value") or 0.0),
        stat_component_source=action_damage_bonus_context.get("stat_component_source"),
        **stat_component_log_fields(action_damage_bonus_context),
        profile_completeness_status=action_damage_bonus_context.get("profile_completeness_status"),
        **mechanic_event_log_fields,
        **echo_set_log_fields,
        aemeath_trailblazing_star_5set_active=AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in active_buff_ids,
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
                **action_damage_bonus_context,
                **mechanic_event_log_fields,
                **echo_set_log_fields,
                "aemeath_trailblazing_star_5set_active": AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in active_buff_ids,
                "active_buff_ids": active_buff_ids,
                "combat_time_start": combat_start_time,
                "combat_time_end": state.combat_time,
            }
        )
    return result


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
        aemeath_trailblazing_star_5set_active=result.aemeath_trailblazing_star_5set_active,
        aemeath_trailblazing_star_5set_applied_before_triggering_damage=(
            result.aemeath_trailblazing_star_5set_applied_before_triggering_damage
        ),
        trailblazing_star_5set_same_action_application=result.trailblazing_star_5set_same_action_application,
        trailblazing_star_5set_application_timing=result.trailblazing_star_5set_application_timing,
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
        mornye_er_excess_percent=result.mornye_er_excess_percent,
        mornye_liberation_crit_rate_bonus=result.mornye_liberation_crit_rate_bonus,
        mornye_liberation_crit_dmg_bonus=result.mornye_liberation_crit_dmg_bonus,
        mornye_interfered_marker_mode=result.mornye_interfered_marker_mode,
        mornye_interfered_amp=result.mornye_interfered_amp,
        mornye_interfered_marker_applied=result.mornye_interfered_marker_applied,
        mornye_expectation_error_mode=result.mornye_expectation_error_mode,
        base_policy_action_id=result.base_policy_action_id,
        optimal_solution_triggered=result.optimal_solution_triggered,
        optimal_solution_trigger_reason=result.optimal_solution_trigger_reason,
        optimal_solution_candidate_id=result.optimal_solution_candidate_id,
        gp_success_modeled=result.gp_success_modeled,
    )
