from __future__ import annotations

from simulator.buff_system import apply_buff, buffed_combat_stats, has_required_buffs, tick_buffs
from simulator.damage_formula import (
    calculate_anomaly_damage,
    calculate_havoc_bane_def_reduction,
    calculate_normal_damage,
    calculate_tune_break_damage,
)
from simulator.models import ActionData, ActionResult, BuffData, CharacterData, CombatState, TimelineEntry
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


def _calculate_action_damage(
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
) -> tuple[float, float, float]:
    if action.character_id is None or action.action_type == "swap":
        return 0.0, 0.0, 0.0

    character = characters[action.character_id]
    stats = buffed_combat_stats(character, state, buffs)
    enemy_def_reduction = state.def_reduction
    if action.anomaly_type == "havoc_bane":
        enemy_def_reduction += calculate_havoc_bane_def_reduction(action.anomaly_stacks)

    normal_damage = 0.0
    if action.damage_multiplier > 0.0:
        normal_damage = calculate_normal_damage(
            skill_multiplier=action.damage_multiplier,
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
            def_reduction=enemy_def_reduction,
            dmg_taken=stats["dmg_taken"],
            final_dmg_bonus=stats["final_dmg_bonus"],
        )

    tune_break_damage = 0.0
    if action.tune_break_multiplier > 0.0:
        tune_break_damage = calculate_tune_break_damage(
            tune_break_multiplier=action.tune_break_multiplier,
            tune_break_boost_points=action.tune_break_boost_points,
            tune_dmg_bonus=state.tune_dmg_bonus,
            enemy_res=state.enemy_res,
            res_pen=state.res_pen,
            attacker_level=int(stats["attacker_level"]),
            enemy_level=state.enemy_level,
            def_ignore=stats["def_ignore"],
            def_reduction=enemy_def_reduction,
        )

    anomaly_damage = 0.0
    if action.anomaly_type is not None:
        anomaly_damage = calculate_anomaly_damage(
            anomaly_type=action.anomaly_type,
            stacks=action.anomaly_stacks,
            enemy_res=state.enemy_res,
            res_pen=state.res_pen,
            attacker_level=int(stats["attacker_level"]),
            enemy_level=state.enemy_level,
            def_ignore=stats["def_ignore"],
            def_reduction=enemy_def_reduction,
        )

    return normal_damage, tune_break_damage, anomaly_damage


def execute_action(
    action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
) -> ActionResult:
    valid, reason = is_action_valid(action, state)
    start_time = state.current_time
    if not valid:
        return ActionResult(
            action_id=action.id,
            action_name=action.name,
            character_id=action.character_id,
            start_time=start_time,
            end_time=start_time,
            damage=0.0,
            valid=False,
            reason=reason,
        )

    # Only buffs active at action start affect this damage. Buffs from this action
    # are applied after the action resolves and affect later actions.
    normal_damage, tune_break_damage, anomaly_damage = _calculate_action_damage(action, state, characters, buffs)
    total_action_damage = normal_damage + tune_break_damage + anomaly_damage

    if action.action_type == "swap" and action.character_id is not None:
        state.active_character_id = action.character_id

    state.total_damage += total_action_damage
    resource_change = apply_resource_changes(state, action, characters)

    state.current_time += action.duration
    reduce_cooldowns(state, action.duration)
    tick_buffs(state, action.duration)

    # Simplified cooldown model: cooldown starts at the end of the action.
    if action.cooldown > 0.0:
        state.cooldowns[action.id] = action.cooldown

    for buff_id in action.applies_buffs:
        apply_buff(state, buffs[buff_id], action.character_id)

    return ActionResult(
        action_id=action.id,
        action_name=action.name,
        character_id=action.character_id,
        start_time=start_time,
        end_time=state.current_time,
        damage=total_action_damage,
        normal_damage=normal_damage,
        tune_break_damage=tune_break_damage,
        anomaly_damage=anomaly_damage,
        total_action_damage=total_action_damage,
        total_damage_after=state.total_damage,
        valid=True,
        resonance_energy_gained=resource_change.resonance_gained,
        resonance_energy_wasted=resource_change.resonance_wasted,
        concerto_energy_gained=resource_change.concerto_gained,
        concerto_energy_wasted=resource_change.concerto_wasted,
    )


def timeline_entry(result: ActionResult, active_character_name: str) -> TimelineEntry:
    return TimelineEntry(
        time_start=result.start_time,
        time_end=result.end_time,
        action_id=result.action_id,
        action_name=result.action_name,
        character_id=result.character_id,
        damage=result.damage,
        normal_damage=result.normal_damage,
        tune_break_damage=result.tune_break_damage,
        anomaly_damage=result.anomaly_damage,
        total_action_damage=result.total_action_damage,
        total_damage_after=result.total_damage_after,
        active_character=active_character_name,
        resonance_energy_gained=result.resonance_energy_gained,
        resonance_energy_wasted=result.resonance_energy_wasted,
        concerto_energy_gained=result.concerto_energy_gained,
        concerto_energy_wasted=result.concerto_energy_wasted,
    )
