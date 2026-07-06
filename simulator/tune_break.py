from __future__ import annotations

from typing import Any

from simulator.damage_formula import calc_def_multiplier, calc_res_multiplier


TUNE_BREAK_BASE_VALUE = 10000.0
TUNE_BREAK_FORMULA_SOURCE = "excel_tune_break_formula_base_10000"


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
