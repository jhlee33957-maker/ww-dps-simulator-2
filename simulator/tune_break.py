from __future__ import annotations

from typing import Any

from simulator.damage_formula import calc_def_multiplier, calc_res_multiplier


TUNE_BREAK_BASE_VALUE = 10000.0
TUNE_BREAK_FORMULA_SOURCE = "excel_tune_break_formula_base_10000"
TUNE_RESPONSE_FORMULA_SOURCE = "excel_tune_response_formula_base_10000"
INTERFERED_MARKER_AMP_SOURCE = "mornye_interfered_marker"
INTERFERED_MARKER_AMP_SOURCE_STATUS = "workbook_confirmed_row_4164"
INTERFERED_MARKER_AMP_SOURCE_REF = "角色-女!4164"


def current_interfered_damage_taken_amp(state: Any) -> float:
    amp = float(getattr(state, "interfered_marker_damage_taken_amp", 0.0) or 0.0)
    if amp <= 0.0:
        return 0.0
    if getattr(state, "target_interfered_state", None) is None:
        return 0.0
    if float(getattr(state, "target_interfered_remaining", 0.0) or 0.0) <= 0.0:
        return 0.0
    return amp


def current_interfered_damage_taken_amp_log_fields(state: Any) -> dict[str, Any]:
    amp = current_interfered_damage_taken_amp(state)
    return {
        "target_damage_taken_amp": amp,
        "target_damage_taken_multiplier": 1.0 + amp,
        "target_damage_taken_amp_source": INTERFERED_MARKER_AMP_SOURCE if amp > 0.0 else None,
        "target_damage_taken_amp_source_status": INTERFERED_MARKER_AMP_SOURCE_STATUS if amp > 0.0 else None,
        "target_damage_taken_amp_source_ref": INTERFERED_MARKER_AMP_SOURCE_REF if amp > 0.0 else None,
    }


def calculate_tune_break_damage_detail(
    *,
    tune_break_multiplier: float,
    additional_tune_break_boost: float = 0.0,
    tune_dmg_bonus: float = 0.0,
    enemy_res: float,
    res_pen: float,
    attacker_level: int,
    enemy_level: int,
    def_ignore: float = 0.0,
    def_reduction: float = 0.0,
    tune_break_base_value: float = TUNE_BREAK_BASE_VALUE,
    tune_break_damage_type: str = "tune_break",
    tune_break_element: str = "unresolved",
    hit_id: str | None = None,
) -> dict[str, Any]:
    res_multiplier = calc_res_multiplier(enemy_res - res_pen)
    def_multiplier = calc_def_multiplier(attacker_level, enemy_level, def_ignore, def_reduction)
    tune_break_boost = 1.0 + additional_tune_break_boost
    tune_dmg_bonus_multiplier = 1.0 + tune_dmg_bonus
    damage = (
        tune_break_base_value
        * tune_break_multiplier
        * tune_break_boost
        * res_multiplier
        * def_multiplier
        * tune_dmg_bonus_multiplier
    )
    return {
        "tune_break_base_value": tune_break_base_value,
        "tune_break_multiplier": tune_break_multiplier,
        "tune_break_boost": tune_break_boost,
        "additional_tune_break_boost": additional_tune_break_boost,
        "tune_dmg_bonus": tune_dmg_bonus_multiplier,
        "sum_tune_dmg_bonus": tune_dmg_bonus,
        "tune_break_res_multiplier": res_multiplier,
        "tune_break_def_multiplier": def_multiplier,
        "tune_break_damage": damage,
        "tune_break_damage_type": tune_break_damage_type,
        "tune_break_element": tune_break_element,
        "tune_break_formula_source": TUNE_BREAK_FORMULA_SOURCE,
        "tune_break_hit_id": hit_id,
        "is_tune_break_damage": True,
    }


def calculate_tune_break_damage(
    *,
    tune_break_multiplier: float,
    additional_tune_break_boost: float = 0.0,
    tune_dmg_bonus: float = 0.0,
    enemy_res: float,
    res_pen: float,
    attacker_level: int,
    enemy_level: int,
    def_ignore: float = 0.0,
    def_reduction: float = 0.0,
    tune_break_base_value: float = TUNE_BREAK_BASE_VALUE,
) -> float:
    return float(
        calculate_tune_break_damage_detail(
            tune_break_multiplier=tune_break_multiplier,
            additional_tune_break_boost=additional_tune_break_boost,
            tune_dmg_bonus=tune_dmg_bonus,
            enemy_res=enemy_res,
            res_pen=res_pen,
            attacker_level=attacker_level,
            enemy_level=enemy_level,
            def_ignore=def_ignore,
            def_reduction=def_reduction,
            tune_break_base_value=tune_break_base_value,
        )["tune_break_damage"]
    )


def calculate_tune_response_damage_detail(
    *,
    tune_response_id: str,
    tune_response_hit_id: str,
    tune_response_multiplier: float,
    additional_tune_response_boost: float = 0.0,
    tune_dmg_bonus: float = 0.0,
    enemy_res: float,
    res_pen: float,
    attacker_level: int,
    enemy_level: int,
    def_ignore: float = 0.0,
    def_reduction: float = 0.0,
    applied_damage_taken_amp: float = 0.0,
    tune_response_base_value: float = TUNE_BREAK_BASE_VALUE,
    tune_response_raw_damage_type: str = "tune_break_response",
    tune_response_element: str = "fusion",
    source_status: str = "workbook_confirmed",
) -> dict[str, Any]:
    res_multiplier = calc_res_multiplier(enemy_res - res_pen)
    def_multiplier = calc_def_multiplier(attacker_level, enemy_level, def_ignore, def_reduction)
    tune_response_boost = 1.0 + additional_tune_response_boost
    tune_dmg_bonus_multiplier = 1.0 + tune_dmg_bonus
    damage_before_amp = (
        tune_response_base_value
        * tune_response_multiplier
        * tune_response_boost
        * res_multiplier
        * def_multiplier
        * tune_dmg_bonus_multiplier
    )
    damage = damage_before_amp * (1.0 + max(0.0, applied_damage_taken_amp))
    return {
        "is_tune_response_damage": True,
        "tune_response_id": tune_response_id,
        "tune_response_hit_id": tune_response_hit_id,
        "tune_response_multiplier": tune_response_multiplier,
        "tune_response_base_value": tune_response_base_value,
        "tune_response_boost": tune_response_boost,
        "additional_tune_response_boost": additional_tune_response_boost,
        "tune_dmg_bonus": tune_dmg_bonus_multiplier,
        "sum_tune_dmg_bonus": tune_dmg_bonus,
        "tune_response_res_multiplier": res_multiplier,
        "tune_response_def_multiplier": def_multiplier,
        "tune_response_element": tune_response_element,
        "tune_response_raw_damage_type": tune_response_raw_damage_type,
        "tune_response_damage_before_damage_taken_amp": damage_before_amp,
        "tune_response_damage": damage,
        "applied_damage_taken_amp": applied_damage_taken_amp,
        "response_damage_receives_interfered_marker_amp": applied_damage_taken_amp > 0.0,
        "response_damage_receives_newly_applied_interfered_marker_amp": False,
        "response_damage_receives_existing_interfered_marker_amp": False,
        "response_damage_receives_new_interfered_marker_amp": False,
        "source_status": source_status,
        "tune_response_formula_source": TUNE_RESPONSE_FORMULA_SOURCE,
    }
