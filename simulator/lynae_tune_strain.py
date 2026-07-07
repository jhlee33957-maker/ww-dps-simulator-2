from __future__ import annotations

from typing import Any

from simulator.buff_system import support_stat_context
from simulator.models import BuffData, CharacterData, CombatState


LYNAE_TUNE_STRAIN_AMP_PER_STACK_PER_BOOST_POINT = 0.0012
LYNAE_TUNE_STRAIN_SOURCE_STATUS = "user_tooltip_confirmed_single_target"
LYNAE_TUNE_STRAIN_SOURCE_REF = "角色-女!2728"


def lynae_tune_strain_max_stacks(mechanics_config: dict[str, Any] | None) -> int:
    lynae_config = dict(((mechanics_config or {}).get("lynae") or {}))
    constellation = max(0, int(lynae_config.get("lynae_constellation", 0) or 0))
    return 2 if constellation >= 2 else 1


def clear_lynae_tune_strain_state(state: CombatState) -> None:
    state.target_tune_strain_interfered_stacks = 0
    state.target_tune_strain_interfered_remaining = 0.0
    state.lynae_tune_strain_damage_amp = 0.0
    state.lynae_tune_strain_damage_multiplier = 1.0
    state.lynae_tune_strain_damage_amp_bonus_damage = 0.0
    state.lynae_tune_strain_source_status = None
    state.lynae_tune_strain_source_ref = None


def refresh_lynae_tune_strain_amp(
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    *,
    time_offset: float = 0.0,
    force_active_buff_ids: set[str] | None = None,
) -> dict[str, Any]:
    stacks = int(getattr(state, "target_tune_strain_interfered_stacks", 0) or 0)
    remaining = float(getattr(state, "target_tune_strain_interfered_remaining", 0.0) or 0.0)
    max_stacks = lynae_tune_strain_max_stacks(getattr(state, "mechanics_config", {}) or {})
    state.target_tune_strain_interfered_max_stacks = max_stacks
    if state.target_interfered_state != "tune_strain_interfered" or remaining <= 0.0 or stacks <= 0:
        clear_lynae_tune_strain_state(state)
        state.target_tune_strain_interfered_max_stacks = max_stacks
        return _log_fields(state, current_boost_points=0.0)

    stacks = min(stacks, max_stacks)
    state.target_tune_strain_interfered_stacks = stacks
    lynae = characters.get("lynae")
    if lynae is None:
        current_boost_points = 0.0
    else:
        current_boost_points = float(
            support_stat_context(
                lynae,
                state,
                buffs,
                time_offset=time_offset,
                force_active_buff_ids=force_active_buff_ids,
            ).get("current_tune_break_boost_points", 0.0)
            or 0.0
        )
    amp = stacks * current_boost_points * LYNAE_TUNE_STRAIN_AMP_PER_STACK_PER_BOOST_POINT
    state.lynae_tune_strain_damage_amp = amp
    state.lynae_tune_strain_damage_multiplier = 1.0 + amp
    state.lynae_tune_strain_source_status = LYNAE_TUNE_STRAIN_SOURCE_STATUS
    state.lynae_tune_strain_source_ref = LYNAE_TUNE_STRAIN_SOURCE_REF
    return _log_fields(state, current_boost_points=current_boost_points)


def apply_lynae_tune_strain_damage_amp(
    damage: float,
    *,
    source_character_id: str | None,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, BuffData],
    time_offset: float = 0.0,
    force_active_buff_ids: set[str] | None = None,
) -> tuple[float, dict[str, Any]]:
    log = refresh_lynae_tune_strain_amp(
        state,
        characters,
        buffs,
        time_offset=time_offset,
        force_active_buff_ids=force_active_buff_ids,
    )
    if source_character_id != "lynae" or damage <= 0.0:
        log["lynae_tune_strain_damage_amp_bonus_damage"] = 0.0
        return damage, log
    multiplier = float(log["lynae_tune_strain_damage_multiplier"])
    if multiplier <= 1.0:
        log["lynae_tune_strain_damage_amp_bonus_damage"] = 0.0
        return damage, log
    amplified = damage * multiplier
    bonus = amplified - damage
    state.lynae_tune_strain_damage_amp_bonus_damage += bonus
    log["lynae_tune_strain_damage_amp_bonus_damage"] = bonus
    return amplified, log


def _log_fields(state: CombatState, *, current_boost_points: float) -> dict[str, Any]:
    return {
        "target_tune_strain_interfered_stacks": int(state.target_tune_strain_interfered_stacks or 0),
        "target_tune_strain_interfered_max_stacks": int(state.target_tune_strain_interfered_max_stacks or 1),
        "target_tune_strain_interfered_remaining": float(state.target_tune_strain_interfered_remaining or 0.0),
        "current_tune_break_boost_points": float(current_boost_points or 0.0),
        "lynae_tune_strain_damage_amp": float(state.lynae_tune_strain_damage_amp or 0.0),
        "lynae_tune_strain_damage_multiplier": float(state.lynae_tune_strain_damage_multiplier or 1.0),
        "lynae_tune_strain_damage_amp_bonus_damage": 0.0,
        "lynae_tune_strain_source_status": state.lynae_tune_strain_source_status,
        "lynae_tune_strain_source_ref": state.lynae_tune_strain_source_ref,
    }
