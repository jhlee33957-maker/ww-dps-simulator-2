from __future__ import annotations

from typing import Any

from simulator.anomaly_system import advance_anomalies, apply_anomaly, get_havoc_bane_def_reduction_at_time
from simulator.buff_system import (
    apply_buff,
    apply_buff_modifiers_to_damage_context,
    buffed_combat_stats,
    damage_amp_for_action,
    has_required_buffs,
    tick_buffs,
)
from simulator.damage_formula import calculate_normal_damage, calculate_tune_break_damage
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
) -> tuple[float, dict]:
    if action.character_id is None or action.action_type == "swap":
        return 0.0, {}

    character = characters[action.character_id]
    stats = buffed_combat_stats(character, state, buffs, time_offset=hit.time)
    damage_amp = damage_amp_for_action(action.character_id, action, state, buffs, time_offset=hit.time)
    havoc_def_reduction = get_havoc_bane_def_reduction_at_time(state, hit.time)
    final_def_reduction = state.def_reduction + havoc_def_reduction

    damage = 0.0
    if hit.damage_category == "normal" and hit.damage_multiplier > 0.0:
        damage = calculate_normal_damage(
            skill_multiplier=hit.damage_multiplier,
            character_base_atk=stats["character_base_atk"],
            weapon_base_atk=stats["weapon_base_atk"],
            atk_percent=stats["atk_percent"],
            flat_atk=stats["flat_atk"],
            dmg_bonus=stats["dmg_bonus"],
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
        "damage_category": hit.damage_category,
        "damage": damage,
        "damage_multiplier": hit.damage_multiplier,
        "tune_break_multiplier": hit.tune_break_multiplier,
        "applied_havoc_bane_def_reduction": havoc_def_reduction,
        "applied_buff_summary": stats.get("active_buff_summary", []),
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
) -> tuple[float, float, list[dict], dict[str, float], float]:
    normal_damage = 0.0
    tune_break_damage = 0.0
    damage_after_cutoff_excluded = 0.0
    hit_details: list[dict] = []
    damage_by_category: dict[str, float] = {}
    has_explicit_hit_timing = bool(action.hits)

    for hit in sorted(action.effective_hits(), key=lambda item: item.time):
        if hit.time > action_time:
            continue
        damage, detail = _calculate_hit_damage(hit, action, state, characters, buffs)
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
        damage_by_category[hit.damage_category] = damage_by_category.get(hit.damage_category, 0.0) + damage
        if hit.damage_category == "normal":
            normal_damage += damage
        elif hit.damage_category == "tune_break":
            tune_break_damage += damage

    return normal_damage, tune_break_damage, hit_details, damage_by_category, damage_after_cutoff_excluded


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
    actor_character_id = active_character_before if action.action_type in {"swap", "wait"} else action.character_id
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

    # Damage events use an action-start state snapshot. Buffs/anomalies applied by
    # this action are added after action_time and do not affect same-action hits.
    normal_damage, tune_break_damage, hit_details, hit_damage_by_category, damage_after_cutoff_excluded = _calculate_hit_damage_totals(
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
    )
    direct_damage = normal_damage + tune_break_damage

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
        active_anomalies_after=active_anomalies_after,
        active_buffs=active_buff_ids,
        applied_buffs=applied_buff_ids,
        valid=True,
        resonance_energy_gained=resource_change.resonance_gained if resource_change is not None else 0.0,
        resonance_energy_wasted=resource_change.resonance_wasted if resource_change is not None else 0.0,
        concerto_before=resource_change.concerto_before if resource_change is not None else 0.0,
        concerto_gain=resource_change.concerto_gained if resource_change is not None else 0.0,
        concerto_after=resource_change.concerto_after if resource_change is not None else 0.0,
        concerto_ready_after=resource_change.concerto_ready_after if resource_change is not None else False,
        concerto_energy_gained=resource_change.concerto_gained if resource_change is not None else 0.0,
        concerto_energy_wasted=resource_change.concerto_wasted if resource_change is not None else 0.0,
    )
    state.action_log.append(result.model_dump(mode="json"))
    if total_action_damage > 0.0 or damage_after_cutoff_excluded > 0.0:
        state.damage_log.append(
            {
                "action_id": action.id,
                "actor_character_id": actor_character_id,
                "damage_before_cutoff": total_action_damage,
                "damage_after_cutoff_excluded": damage_after_cutoff_excluded,
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
        outgoing_outro_applied=result.outgoing_outro_applied,
        transition_events=result.transition_events,
        outgoing_outro_event_id=result.outgoing_outro_event_id,
        incoming_intro_event_id=result.incoming_intro_event_id,
        fallback_swap_used=result.fallback_swap_used,
        swap_timing_is_placeholder=result.swap_timing_is_placeholder,
        swap_timing_source=result.swap_timing_source,
        transition_warnings=result.transition_warnings,
        active_character=active_character_name,
        resonance_energy_gained=result.resonance_energy_gained,
        resonance_energy_wasted=result.resonance_energy_wasted,
        concerto_before=result.concerto_before,
        concerto_gain=result.concerto_gain,
        concerto_after=result.concerto_after,
        concerto_ready_after=result.concerto_ready_after,
        concerto_energy_gained=result.concerto_energy_gained,
        concerto_energy_wasted=result.concerto_energy_wasted,
        mechanic_debug_after=result.mechanic_debug_after,
    )
