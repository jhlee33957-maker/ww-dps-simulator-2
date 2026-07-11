from __future__ import annotations

from dataclasses import dataclass

from simulator.damage_formula import calculate_havoc_bane_def_reduction
from simulator.models import CombatState
from simulator.tune_break import current_interfered_damage_taken_amp


@dataclass(frozen=True)
class ActionStartEffectSnapshot:
    active_buff_ids: frozenset[str]
    active_buff_remaining: dict[str, float]
    target_damage_taken_amp: float
    havoc_bane_def_reduction: float

    def buff_active(self, buff_id: str) -> bool:
        return buff_id in self.active_buff_ids

    def buff_remaining(self, buff_id: str) -> float:
        return float(self.active_buff_remaining.get(buff_id, 0.0) or 0.0)


def capture_action_start_effect_snapshot(state: CombatState) -> ActionStartEffectSnapshot:
    active_buff_remaining = {
        active.buff_id: float(active.remaining_duration)
        for active in state.active_buffs
        if active.remaining_duration > 0.0
    }
    havoc_bane = state.active_anomalies.get("havoc_bane")
    havoc_bane_def_reduction = (
        calculate_havoc_bane_def_reduction(havoc_bane.stacks)
        if havoc_bane is not None and havoc_bane.remaining_duration > 0.0
        else 0.0
    )
    return ActionStartEffectSnapshot(
        active_buff_ids=frozenset(active_buff_remaining),
        active_buff_remaining=active_buff_remaining,
        target_damage_taken_amp=current_interfered_damage_taken_amp(state),
        havoc_bane_def_reduction=havoc_bane_def_reduction,
    )
