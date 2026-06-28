from __future__ import annotations

from simulator.buff_system import apply_buff, has_required_buffs, tick_buffs
from simulator.damage_formula import expected_damage
from simulator.models import ActionData, ActionResult, BuffData, CharacterData, CombatState, TimelineEntry
from simulator.resource_system import apply_resource_changes, can_pay_resources


def is_action_valid(action: ActionData, state: CombatState) -> tuple[bool, str | None]:
    if action.action_type == "wait":
        return True, None

    if action.action_type != "swap" and action.character_id != state.active_character_id:
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

    if action.action_type == "swap" and action.character_id is not None:
        state.active_character_id = action.character_id

    damage = 0.0
    if action.character_id is not None and action.action_type != "swap":
        damage = expected_damage(characters[action.character_id], action, state, buffs)

    state.total_damage += damage
    apply_resource_changes(state, action)

    if action.cooldown > 0.0:
        state.cooldowns[action.id] = action.cooldown

    for buff_id in action.applies_buffs:
        apply_buff(state, buffs[buff_id], action.character_id)

    state.current_time += action.duration
    reduce_cooldowns(state, action.duration)
    tick_buffs(state, action.duration)

    return ActionResult(
        action_id=action.id,
        action_name=action.name,
        character_id=action.character_id,
        start_time=start_time,
        end_time=state.current_time,
        damage=damage,
        valid=True,
    )


def timeline_entry(result: ActionResult, active_character_name: str) -> TimelineEntry:
    return TimelineEntry(
        time_start=result.start_time,
        time_end=result.end_time,
        action_id=result.action_id,
        action_name=result.action_name,
        character_id=result.character_id,
        damage=result.damage,
        active_character=active_character_name,
    )
