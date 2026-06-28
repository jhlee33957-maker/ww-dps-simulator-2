from __future__ import annotations

from simulator.models import ActionData, CombatState


def can_pay_resources(state: CombatState, action: ActionData) -> bool:
    if action.action_type != "resonance_liberation" or action.character_id is None:
        return True
    return state.resonance_energy.get(action.character_id, 0.0) >= action.resonance_energy_cost


def apply_resource_changes(state: CombatState, action: ActionData) -> None:
    if action.character_id is None:
        return

    character_id = action.character_id
    state.resonance_energy[character_id] = max(
        0.0,
        state.resonance_energy.get(character_id, 0.0) - action.resonance_energy_cost,
    )
    state.resonance_energy[character_id] += action.resonance_energy_gain
    state.concerto_energy[character_id] = min(
        100.0,
        state.concerto_energy.get(character_id, 0.0) + action.concerto_energy_gain,
    )
