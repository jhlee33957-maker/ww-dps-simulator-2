from __future__ import annotations

from typing import Any

from simulator.anomaly_system import advance_anomalies, apply_anomaly, get_havoc_bane_def_reduction_at_time
from simulator.buff_system import apply_buff, buffed_combat_stats, has_required_buffs, tick_buffs
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

    if state.cooldowns.get(action.id, 0.0) > 0.0:
        return False, "Action is on cooldown."

    if not can_pay_resources(state, action):
        return False, "Not enough resonance energy."

    if not has_required_buffs(state, action.required_buffs):
        return False, "Required buff is missing."

    return True, None


def reduce_cooldowns(state: CombatState, elapsed: float) -> None:
    for action_id, remaining in list(state.cooldowns.items()):
        updated = max(0.0, remaining - elapsed)
        if updated > 0.0:
            state.cooldowns[action_id] = updated
        else:
            del state.cooldowns[action_id]


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

    detail = {
        "hit_time": hit.time,
        "damage_category": hit.damage_category,
        "damage": damage,
        "damage_multiplier": hit.damage_multiplier,
        "tune_break_multiplier": hit.tune_break_multiplier,
        "applied_havoc_bane_def_reduction": havoc_def_reduction,
        "applied_buff_summary": stats.get("active_buff_summary", []),
        "name": hit.name,
    }
    return damage, detail


def _calculate_hit_damage_totals(
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
) -> tuple[float, float, list[dict], dict[str, float]]:
    normal_damage = 0.0
    tune_break_damage = 0.0
    hit_details: list[dict] = []
    damage_by_category: dict[str, float] = {}

    for hit in sorted(action.effective_hits(), key=lambda item: item.time):
        if hit.time > action.effective_action_time:
            continue
        damage, detail = _calculate_hit_damage(hit, action, state, characters, buffs)
        if detail:
            hit_details.append(detail)
        damage_by_category[hit.damage_category] = damage_by_category.get(hit.damage_category, 0.0) + damage
        if hit.damage_category == "normal":
            normal_damage += damage
        elif hit.damage_category == "tune_break":
            tune_break_damage += damage

    return normal_damage, tune_break_damage, hit_details, damage_by_category


def execute_action(
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    mechanic: Any | None = None,
) -> ActionResult:
    valid, reason = is_action_valid(action, state)
    start_time = state.current_time
    action_time = action.effective_action_time
    if not valid:
        return ActionResult(
            action_id=action.id,
            action_name=action.name,
            character_id=action.character_id,
            start_time=start_time,
            end_time=start_time,
            action_time=0.0,
            damage=0.0,
            valid=False,
            reason=reason,
        )

    if mechanic is not None:
        mechanic.before_action(state, action)

    # Damage events use an action-start state snapshot. Buffs/anomalies applied by
    # this action are added after action_time and do not affect same-action hits.
    normal_damage, tune_break_damage, hit_details, hit_damage_by_category = _calculate_hit_damage_totals(
        action, state, characters, buffs
    )
    direct_damage = normal_damage + tune_break_damage

    if action.action_type == "swap" and action.character_id is not None:
        state.active_character_id = action.character_id

    state.total_damage += direct_damage
    resource_change = apply_resource_changes(state, action, characters)

    state.current_time += action_time
    reduce_cooldowns(state, action_time)
    tick_buffs(state, action_time)
    anomaly_tick_damage, anomaly_damage_by_type = advance_anomalies(state, action_time)
    state.total_damage += anomaly_tick_damage

    total_action_damage = direct_damage + anomaly_tick_damage

    for buff_id in action.applies_buffs:
        apply_buff(state, buffs[buff_id], action.character_id)
    apply_anomaly(state, action)

    # Simplified cooldown model: cooldown starts at the end of the action.
    if action.cooldown > 0.0:
        state.cooldowns[action.id] = action.cooldown

    active_anomalies_after = {
        anomaly_type: anomaly.stacks
        for anomaly_type, anomaly in state.active_anomalies.items()
        if anomaly.remaining_duration > 0.0
    }

    result = ActionResult(
        action_id=action.id,
        action_name=action.name,
        character_id=action.character_id,
        start_time=start_time,
        end_time=state.current_time,
        action_time=action_time,
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
        valid=True,
        resonance_energy_gained=resource_change.resonance_gained,
        resonance_energy_wasted=resource_change.resonance_wasted,
        concerto_energy_gained=resource_change.concerto_gained,
        concerto_energy_wasted=resource_change.concerto_wasted,
    )
    if mechanic is not None:
        mechanic.after_action(state, action, result)
    return result


def timeline_entry(result: ActionResult, active_character_name: str) -> TimelineEntry:
    return TimelineEntry(
        time_start=result.start_time,
        time_end=result.end_time,
        action_id=result.action_id,
        action_name=result.action_name,
        character_id=result.character_id,
        action_time=result.action_time,
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
        active_character=active_character_name,
        resonance_energy_gained=result.resonance_energy_gained,
        resonance_energy_wasted=result.resonance_energy_wasted,
        concerto_energy_gained=result.concerto_energy_gained,
        concerto_energy_wasted=result.concerto_energy_wasted,
    )
