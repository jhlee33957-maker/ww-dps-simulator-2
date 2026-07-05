from __future__ import annotations

from simulator.buff_system import buffed_combat_stats
from simulator.build_profiles import damage_bonus_breakdown
from simulator.models import ActionData, BuffData, CharacterData, CombatState


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def calc_res_multiplier(total_res: float) -> float:
    if total_res < 0.0:
        return 1.0 - total_res / 2.0
    if total_res < 0.8:
        return 1.0 - total_res
    return 1.0 / (1.0 + 5.0 * total_res)


def calc_def_multiplier(
    attacker_level: int,
    enemy_level: int,
    def_ignore: float = 0.0,
    def_reduction: float = 0.0,
) -> float:
    def_ignore = _clamp(def_ignore, 0.0, 1.0)
    def_reduction = _clamp(def_reduction, 0.0, 1.0)
    attacker_term = 800.0 + 8.0 * attacker_level
    enemy_term = (792.0 + 8.0 * enemy_level) * (1.0 - def_ignore) * (1.0 - def_reduction)
    denominator = attacker_term + max(0.0, enemy_term)
    if denominator <= 0.0:
        return 1.0
    return attacker_term / denominator


def calculate_normal_damage(
    *,
    skill_multiplier: float,
    character_base_atk: float,
    weapon_base_atk: float,
    atk_percent: float,
    flat_atk: float,
    dmg_bonus: float,
    crit_rate: float,
    crit_damage: float,
    boost: float,
    enemy_res: float,
    res_pen: float,
    attacker_level: int,
    enemy_level: int,
    def_ignore: float = 0.0,
    def_reduction: float = 0.0,
    dmg_taken: float = 0.0,
    final_dmg_bonus: float = 0.0,
    effective_attack: float | None = None,
) -> float:
    base_atk = max(1.0, character_base_atk + weapon_base_atk)
    attack = float(effective_attack) if effective_attack is not None else base_atk * (1.0 + atk_percent) + flat_atk
    expected_crit = 1.0 + _clamp(crit_rate, 0.0, 1.0) * (max(1.0, crit_damage) - 1.0)
    return (
        skill_multiplier
        * attack
        * (1.0 + dmg_bonus)
        * expected_crit
        * (1.0 + boost)
        * calc_res_multiplier(enemy_res - res_pen)
        * calc_def_multiplier(attacker_level, enemy_level, def_ignore, def_reduction)
        * (1.0 + dmg_taken)
        * (1.0 + final_dmg_bonus)
    )


def calculate_tune_break_damage(
    *,
    tune_break_multiplier: float,
    tune_break_base: float = 10000.0,
    tune_break_boost_points: float = 0.0,
    tune_dmg_bonus: float = 0.0,
    enemy_res: float,
    res_pen: float,
    attacker_level: int,
    enemy_level: int,
    def_ignore: float = 0.0,
    def_reduction: float = 0.0,
) -> float:
    tune_break_boost = (100.0 + tune_break_boost_points) / 100.0
    return (
        tune_break_base
        * tune_break_multiplier
        * tune_break_boost
        * calc_res_multiplier(enemy_res - res_pen)
        * calc_def_multiplier(attacker_level, enemy_level, def_ignore, def_reduction)
        * (1.0 + tune_dmg_bonus)
    )


def calculate_havoc_bane_def_reduction(stacks: int) -> float:
    return max(0, stacks) * 0.02


def calculate_anomaly_damage(
    *,
    anomaly_type: str,
    stacks: int,
    enemy_res: float,
    res_pen: float,
    attacker_level: int,
    enemy_level: int,
    def_ignore: float = 0.0,
    def_reduction: float = 0.0,
) -> float:
    stacks = max(0, stacks)
    if stacks <= 0:
        return 0.0

    if anomaly_type == "aero_erosion":
        base_value = 1654.0 if stacks == 1 else 4134.0 * (stacks - 1)
    elif anomaly_type == "spectro_frazzle":
        base_value = 898.0 * 1.235 + 898.0 * max(stacks - 1, 0)
    elif anomaly_type == "electro_flare":
        base_value = 343.0 + 1494.0 * stacks
        if stacks > 10:
            base_value *= 1.0 + (stacks - 10) / 3.0
    elif anomaly_type == "havoc_bane":
        return 0.0
    else:
        raise ValueError(f"Unsupported anomaly type: {anomaly_type}")

    return (
        base_value
        * calc_def_multiplier(attacker_level, enemy_level, def_ignore, def_reduction)
        * calc_res_multiplier(enemy_res - res_pen)
    )


def expected_damage(
    character: CharacterData,
    action: ActionData,
    state: CombatState,
    buffs: dict[str, BuffData],
) -> float:
    if action.damage_multiplier <= 0.0:
        return 0.0
    stats = buffed_combat_stats(character, state, buffs)
    damage_bonus_context = damage_bonus_breakdown(
        character,
        action,
        additive_buff_bonus=float(stats.get("damage_bonus_buff", 0.0)),
    )
    return calculate_normal_damage(
        skill_multiplier=action.damage_multiplier,
        character_base_atk=stats["character_base_atk"],
        weapon_base_atk=stats["weapon_base_atk"],
        atk_percent=stats["atk_percent"],
        flat_atk=stats["flat_atk"],
        effective_attack=stats["effective_attack"],
        dmg_bonus=float(damage_bonus_context["effective_damage_bonus"]),
        crit_rate=stats["crit_rate"],
        crit_damage=stats["crit_damage"],
        boost=stats["boost"],
        enemy_res=state.enemy_res,
        res_pen=state.res_pen,
        attacker_level=int(stats["attacker_level"]),
        enemy_level=state.enemy_level,
        def_ignore=stats["def_ignore"],
        def_reduction=state.def_reduction,
        dmg_taken=state.dmg_taken,
        final_dmg_bonus=stats["final_dmg_bonus"],
    )
