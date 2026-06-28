from __future__ import annotations

from simulator.damage_formula import calculate_anomaly_damage, calculate_havoc_bane_def_reduction
from simulator.models import ActionData, AnomalyState, CombatState

MAX_ANOMALY_STACKS = 99
TICKING_ANOMALIES = {"aero_erosion", "spectro_frazzle", "electro_flare"}


def apply_anomaly(state: CombatState, action: ActionData) -> None:
    if action.applies_anomaly_type is None or action.applies_anomaly_stacks <= 0:
        return

    anomaly_type = action.applies_anomaly_type
    existing = state.active_anomalies.get(anomaly_type)
    if existing is None:
        state.active_anomalies[anomaly_type] = AnomalyState(
            anomaly_type=anomaly_type,
            stacks=min(MAX_ANOMALY_STACKS, action.applies_anomaly_stacks),
            remaining_duration=action.anomaly_duration,
            tick_interval=action.anomaly_tick_interval,
            tick_timer=action.anomaly_tick_interval,
        )
        return

    existing.stacks = min(MAX_ANOMALY_STACKS, existing.stacks + action.applies_anomaly_stacks)
    existing.remaining_duration = action.anomaly_duration
    existing.tick_interval = action.anomaly_tick_interval
    existing.tick_timer = action.anomaly_tick_interval


def get_havoc_bane_def_reduction(state: CombatState) -> float:
    havoc_bane = state.active_anomalies.get("havoc_bane")
    if havoc_bane is None or havoc_bane.remaining_duration <= 0.0:
        return 0.0
    return calculate_havoc_bane_def_reduction(havoc_bane.stacks)


def advance_anomalies(state: CombatState, duration: float) -> tuple[float, dict[str, float]]:
    total_damage = 0.0
    damage_by_type: dict[str, float] = {}
    expired: list[str] = []

    for anomaly_type, anomaly in list(state.active_anomalies.items()):
        elapsed = 0.0
        while elapsed < duration and anomaly.remaining_duration > 0.0:
            step = min(anomaly.tick_timer, duration - elapsed, anomaly.remaining_duration)
            elapsed += step
            anomaly.remaining_duration = max(0.0, anomaly.remaining_duration - step)
            anomaly.tick_timer = max(0.0, anomaly.tick_timer - step)

            if anomaly.tick_timer <= 0.0:
                damage = _tick_damage(state, anomaly)
                if damage > 0.0:
                    total_damage += damage
                    damage_by_type[anomaly_type] = damage_by_type.get(anomaly_type, 0.0) + damage
                anomaly.tick_timer = anomaly.tick_interval

        if anomaly.remaining_duration <= 0.0:
            expired.append(anomaly_type)

    for anomaly_type in expired:
        del state.active_anomalies[anomaly_type]

    return total_damage, damage_by_type


def _tick_damage(state: CombatState, anomaly: AnomalyState) -> float:
    if anomaly.anomaly_type not in TICKING_ANOMALIES:
        return 0.0
    return calculate_anomaly_damage(
        anomaly_type=anomaly.anomaly_type,
        stacks=anomaly.stacks,
        enemy_res=state.enemy_res,
        res_pen=state.res_pen,
        attacker_level=90,
        enemy_level=state.enemy_level,
        def_ignore=0.0,
        def_reduction=state.def_reduction + get_havoc_bane_def_reduction(state),
    )
