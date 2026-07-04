from __future__ import annotations

from typing import Any

from simulator.models import ActionData, CharacterData, CombatState, ResourceChange

CONCERTO_ENERGY_MAX = 100.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def ensure_concerto_state(
    character_state: dict[str, Any],
    *,
    energy: float | None = None,
    cap: float = CONCERTO_ENERGY_MAX,
) -> dict[str, Any]:
    concerto_cap = float(character_state.get("concerto_energy_cap", cap) or cap)
    concerto_cap = max(0.001, concerto_cap)
    current = float(character_state.get("concerto_energy", 0.0) if energy is None else energy)
    current = _clamp(current, 0.0, concerto_cap)
    character_state["concerto_energy"] = current
    character_state["concerto_energy_cap"] = concerto_cap
    character_state["concerto_ready"] = current >= concerto_cap
    return character_state


def get_concerto_energy(character_state: dict[str, Any]) -> float:
    ensure_concerto_state(character_state)
    return float(character_state["concerto_energy"])


def add_concerto_energy(character_state: dict[str, Any], amount: float) -> tuple[float, float, float, bool, float]:
    ensure_concerto_state(character_state)
    before = float(character_state["concerto_energy"])
    cap = float(character_state["concerto_energy_cap"])
    uncapped = before + float(amount)
    after = _clamp(uncapped, 0.0, cap)
    wasted = max(0.0, uncapped - cap)
    gained = after - before
    character_state["concerto_energy"] = after
    character_state["concerto_ready"] = after >= cap
    return before, gained, after, bool(character_state["concerto_ready"]), wasted


def is_concerto_ready(character_state: dict[str, Any]) -> bool:
    ensure_concerto_state(character_state)
    return bool(character_state["concerto_ready"])


def consume_concerto(character_state: dict[str, Any]) -> float:
    ensure_concerto_state(character_state)
    before = float(character_state["concerto_energy"])
    character_state["concerto_energy"] = 0.0
    character_state["concerto_ready"] = False
    return before


def sync_concerto_state(
    state: CombatState,
    character_id: str,
    *,
    default_cap: float = CONCERTO_ENERGY_MAX,
) -> dict[str, Any]:
    character_state = state.character_states.setdefault(character_id, {})
    energy = state.concerto_energy.get(character_id, character_state.get("concerto_energy", 0.0))
    ensure_concerto_state(character_state, energy=float(energy), cap=default_cap)
    state.concerto_energy[character_id] = float(character_state["concerto_energy"])
    return character_state


def initialize_concerto_states(
    state: CombatState,
    character_ids: list[str],
    *,
    default_cap: float = CONCERTO_ENERGY_MAX,
) -> None:
    for character_id in character_ids:
        sync_concerto_state(state, character_id, default_cap=default_cap)


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
    base_resonance_energy_gain = float(action.resonance_energy_gain)
    energy_regen = float(character.energy_regen)
    final_resonance_energy_gain = base_resonance_energy_gain * energy_regen

    resonance_after_cost = max(
        0.0,
        state.resonance_energy.get(character_id, 0.0) - action.resonance_energy_cost,
    )
    resonance_uncapped = resonance_after_cost + final_resonance_energy_gain
    resonance_capped = min(character.resonance_energy_max, resonance_uncapped)
    resonance_wasted = max(0.0, resonance_uncapped - resonance_capped)
    resonance_gained = max(0.0, final_resonance_energy_gain - resonance_wasted)

    character_state = sync_concerto_state(state, character_id)
    concerto_before, concerto_gained, concerto_capped, concerto_ready_after, concerto_wasted = add_concerto_energy(
        character_state,
        action.concerto_energy_gain,
    )

    state.resonance_energy[character_id] = resonance_capped
    state.concerto_energy[character_id] = concerto_capped
    state.wasted_resonance_energy[character_id] = (
        state.wasted_resonance_energy.get(character_id, 0.0) + resonance_wasted
    )
    state.wasted_concerto_energy[character_id] = (
        state.wasted_concerto_energy.get(character_id, 0.0) + concerto_wasted
    )

    return ResourceChange(
        base_resonance_energy_gain=base_resonance_energy_gain,
        energy_regen=energy_regen,
        final_resonance_energy_gain=final_resonance_energy_gain,
        resonance_gained=resonance_gained,
        resonance_wasted=resonance_wasted,
        concerto_before=concerto_before,
        concerto_gained=concerto_gained,
        concerto_wasted=concerto_wasted,
        concerto_after=concerto_capped,
        concerto_ready_after=concerto_ready_after,
    )
