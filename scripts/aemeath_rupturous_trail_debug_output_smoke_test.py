from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from characters.aemeath import AemeathMechanic
from simulator.simulation import Simulation


def assert_close(actual: float, expected: float) -> None:
    assert abs(actual - expected) < 1e-9, f"{actual} != {expected}"


def ready_seraphic(sim: Simulation, *, preserve: bool) -> None:
    data = sim.state.character_mechanics_state["aemeath"]
    data["form"] = "aemeath"
    data["synchronization_rate"] = 100.0
    data["seraphic_duo_remaining"] = 5.0
    data["forte_enhancement_stacks"] = 2
    data["forte_enhancement_remaining"] = 30.0
    data["trail_no_cost_remaining"] = 30.0 if preserve else 0.0
    sim.state.rupturous_trail_stacks = 30
    sim.state.rupturous_trail_remaining = 30.0


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    mechanic = AemeathMechanic()
    ready_seraphic(sim, preserve=True)

    debug = mechanic.get_debug_state(sim.state)
    assert debug["target_rupturous_trail_stacks"] == 30
    assert debug["target_rupturous_trail_remaining"] == 30.0
    assert debug["target_rupturous_trail_max_stacks"] == 30
    assert debug["rupturous_trail_state_source"] == "CombatState"
    assert "rupturous_trail_stacks" not in debug
    assert "rupturous_trail_remaining" not in debug
    assert "rupturous_trail_max_stacks" not in debug
    assert debug["forte_enhancement_stacks"] == 2
    assert debug["trail_no_cost_remaining"] == 30.0

    assert sim.execute_action("aemeath_seraphic_duet_overturn")
    first = sim.timeline[-1]
    first_event = first.generated_mechanic_damage_events[0]
    assert first_event["trail_stack_snapshot"] == 30
    assert_close(first_event["trail_stack_factor"], 2.2)
    assert first_event["trail_preservation_active"] is True
    assert first_event["trail_consumed"] is False
    assert first_event["repeat_count"] == 10
    assert_close(first_event["base_multiplier_per_hit"], 1.0935)
    assert_close(first_event["total_extra_tune_multiplier"], 24.057)
    assert first_event["stacks_after"] == 30
    assert first_event["trail_preservation_after"] is False

    data = sim.state.character_mechanics_state["aemeath"]
    data["form"] = "aemeath"
    data["synchronization_rate"] = 100.0
    data["seraphic_duo_remaining"] = 5.0
    sim.state.cooldowns.clear()
    assert sim.execute_action("aemeath_seraphic_duet_overturn")
    second = sim.timeline[-1]
    second_event = second.generated_mechanic_damage_events[0]
    assert second_event["trail_stack_snapshot"] == 30
    assert second_event["trail_consumed"] is True
    assert second_event["stacks_after"] == 0
    assert sim.state.rupturous_trail_stacks == 0
    assert sim.state.rupturous_trail_remaining == 0.0
    print("aemeath_rupturous_trail_debug_output_smoke_test ok")


if __name__ == "__main__":
    main()
