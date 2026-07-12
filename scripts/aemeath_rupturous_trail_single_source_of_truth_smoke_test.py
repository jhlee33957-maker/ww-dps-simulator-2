from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from characters.aemeath import AemeathMechanic
from simulator.models import CombatState
from simulator.simulation import Simulation


def ready(sim: Simulation) -> None:
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0


def test_legacy_personal_state_is_ignored() -> None:
    state = CombatState(active_character_id="aemeath", party_members=["aemeath"])
    state.rupturous_trail_stacks = 20
    state.rupturous_trail_remaining = 12.0
    state.character_mechanics_state["aemeath"] = {
        "rupturous_trail_stacks": 99,
        "rupturous_trail_remaining": 99.0,
        "rupturous_trail_max_stacks": 99,
    }
    mechanic = AemeathMechanic()
    mechanic.initialize_state(state)
    personal = state.character_mechanics_state["aemeath"]
    assert "rupturous_trail_stacks" not in personal
    assert "rupturous_trail_remaining" not in personal
    assert "rupturous_trail_max_stacks" not in personal
    assert state.rupturous_trail_stacks == 20
    assert state.rupturous_trail_remaining == 12.0


def test_party_responses_write_only_target_state() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    sim.state.character_mechanics_state["aemeath"]["rupturous_trail_stacks"] = 99
    ready(sim)
    assert sim.execute_action("mornye_tune_break")
    assert sim.state.rupturous_trail_stacks == 30
    assert sim.state.rupturous_trail_remaining == 30.0
    personal = sim.state.character_mechanics_state["aemeath"]
    assert "rupturous_trail_stacks" not in personal
    assert "rupturous_trail_remaining" not in personal
    assert "rupturous_trail_max_stacks" not in personal
    assert len(sim.state.rupturous_trail_event_log) == 3


def main() -> None:
    test_legacy_personal_state_is_ignored()
    test_party_responses_write_only_target_state()
    print("aemeath_rupturous_trail_single_source_of_truth_smoke_test ok")


if __name__ == "__main__":
    main()
