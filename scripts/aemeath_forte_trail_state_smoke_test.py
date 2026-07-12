from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from characters.aemeath import AemeathMechanic
from simulator.models import CombatState


def make_state() -> CombatState:
    return CombatState(active_character_id="aemeath", party_members=["aemeath"])


def test_trail_state_clamps_and_expires() -> None:
    mechanic = AemeathMechanic()
    state = make_state()
    state.rupturous_trail_stacks = 30
    state.rupturous_trail_remaining = 2.0
    state.character_mechanics_state["aemeath"] = {
        "fusion_trail_stacks": 99,
        "fusion_trail_max_stacks": 4,
        "fusion_trail_remaining": 3.0,
        "forte_enhancement_stacks": 99,
        "forte_enhancement_max_stacks": 2,
        "forte_enhancement_remaining": 2.0,
        "trail_no_cost_remaining": 3.0,
    }
    mechanic.initialize_state(state)
    data = state.character_mechanics_state["aemeath"]
    assert data["rupturous_trail_max_stacks"] == 30
    assert data["fusion_trail_stacks"] == 4
    assert data["forte_enhancement_stacks"] == 2

    mechanic.advance_time(state, 1.0)
    state.rupturous_trail_remaining = max(0.0, state.rupturous_trail_remaining - 1.0)
    assert state.rupturous_trail_stacks == 30
    assert state.rupturous_trail_remaining == 1.0
    assert data["fusion_trail_stacks"] == 4
    assert data["fusion_trail_remaining"] == 2.0
    assert data["forte_enhancement_stacks"] == 2
    assert data["forte_enhancement_remaining"] == 1.0
    assert data["trail_no_cost_remaining"] == 2.0

    mechanic.advance_time(state, 1.0)
    state.rupturous_trail_remaining = max(0.0, state.rupturous_trail_remaining - 1.0)
    if state.rupturous_trail_remaining <= 0.0:
        state.rupturous_trail_stacks = 0
    assert state.rupturous_trail_stacks == 0
    assert state.rupturous_trail_remaining == 0.0
    assert data["fusion_trail_stacks"] == 4
    assert data["fusion_trail_remaining"] == 1.0
    assert data["forte_enhancement_stacks"] == 0
    assert data["forte_enhancement_remaining"] == 0.0
    assert data["trail_no_cost_remaining"] == 1.0

    mechanic.advance_time(state, 1.0)
    assert data["fusion_trail_stacks"] == 0
    assert data["fusion_trail_remaining"] == 0.0


def test_debug_state_exposes_single_target_trail_scaffold() -> None:
    mechanic = AemeathMechanic()
    state = make_state()
    mechanic.initialize_state(state)
    debug = mechanic.get_debug_state(state)
    assert debug["single_target_aemeath_forte_trail_state"] is True
    assert "target_rupturous_trail_stacks" in debug
    assert "fusion_trail_stacks" in debug
    assert "forte_enhancement_stacks" in debug
    assert "trail_no_cost_remaining" in debug
    assert "forte_unresolved_runtime_notes" in debug


def main() -> None:
    test_trail_state_clamps_and_expires()
    test_debug_state_exposes_single_target_trail_scaffold()
    print("aemeath_forte_trail_state_smoke_test ok")


if __name__ == "__main__":
    main()
