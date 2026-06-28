from __future__ import annotations

from simulator.models import ActionData, CharacterData, CombatState, ResourceChange

CONCERTO_ENERGY_MAX = 100.0


def can_pay_resources(state: CombatState, action: ActionData) -> bool:
    if action.action_type != "resonance_liberation" or action.character_id is None:
        return True
    return state.resonance_energy.get(action.character_id, 0.0) >= action.resonance_energy_cost


def apply_resource_changes(
    state: CombatState,
    action: ActionData,
    characters: dict[str, CharacterData],
) -> ResourceChange:
    if action.character_id is None:
        return ResourceChange()

    character_id = action.character_id
    character = characters[character_id]

    resonance_after_cost = max(
        0.0,
        state.resonance_energy.get(character_id, 0.0) - action.resonance_energy_cost,
    )
    resonance_uncapped = resonance_after_cost + action.resonance_energy_gain
    resonance_capped = min(character.resonance_energy_max, resonance_uncapped)
    resonance_wasted = max(0.0, resonance_uncapped - resonance_capped)
    resonance_gained = action.resonance_energy_gain - resonance_wasted

    concerto_before = state.concerto_energy.get(character_id, 0.0)
    concerto_uncapped = concerto_before + action.concerto_energy_gain
    concerto_capped = min(CONCERTO_ENERGY_MAX, concerto_uncapped)
    concerto_wasted = max(0.0, concerto_uncapped - concerto_capped)
    concerto_gained = action.concerto_energy_gain - concerto_wasted

    state.resonance_energy[character_id] = resonance_capped
    state.concerto_energy[character_id] = concerto_capped
    state.wasted_resonance_energy[character_id] = (
        state.wasted_resonance_energy.get(character_id, 0.0) + resonance_wasted
    )
    state.wasted_concerto_energy[character_id] = (
        state.wasted_concerto_energy.get(character_id, 0.0) + concerto_wasted
    )

    return ResourceChange(
        resonance_gained=resonance_gained,
        resonance_wasted=resonance_wasted,
        concerto_gained=concerto_gained,
        concerto_wasted=concerto_wasted,
    )
