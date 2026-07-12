from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def assert_close(actual: float, expected: float) -> None:
    assert abs(actual - expected) < 1e-9, f"{actual} != {expected}"


def run_seraphic(stacks: int, *, enhanced: bool) -> object:
    sim = Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
    )
    data = sim.state.character_mechanics_state["aemeath"]
    data["form"] = "aemeath"
    data["synchronization_rate"] = 100.0
    data["seraphic_duo_remaining"] = 5.0
    if enhanced:
        data["forte_enhancement_stacks"] = 2
        data["forte_enhancement_remaining"] = 30.0
    sim.state.rupturous_trail_stacks = stacks
    sim.state.rupturous_trail_remaining = 30.0 if stacks else 0.0
    assert sim.execute_action("aemeath_seraphic_duet_overturn")
    return sim.timeline[-1]


def main() -> None:
    normal = {0: 5.4675, 10: 7.6545, 20: 9.8415, 30: 12.0285}
    enhanced = {0: 10.935, 10: 15.309, 20: 19.683, 30: 24.057}
    for stacks, expected in normal.items():
        row = run_seraphic(stacks, enhanced=False)
        assert row.aemeath_seraphic_duet_followup_repeat_count == 5
        assert_close(row.aemeath_seraphic_duet_total_extra_tune_multiplier, expected)
        event = row.generated_mechanic_damage_events[0]
        assert event["trail_stack_snapshot"] == stacks
        assert event["trail_stack_factor"] == 1.0 + 0.04 * stacks
        assert event["trail_preservation_active"] is False
        assert event["trail_consumed"] is (stacks > 0)
        assert event["repeat_count"] == 5
        assert event["base_multiplier_per_hit"] == 1.0935
        assert event["stacks_after"] == 0
        assert_close(event["total_extra_tune_multiplier"], expected)
    for stacks, expected in enhanced.items():
        row = run_seraphic(stacks, enhanced=True)
        assert row.aemeath_seraphic_duet_followup_repeat_count == 10
        assert_close(row.aemeath_seraphic_duet_total_extra_tune_multiplier, expected)
        event = row.generated_mechanic_damage_events[0]
        assert event["trail_stack_snapshot"] == stacks
        assert event["repeat_count"] == 10
        assert event["stacks_after"] == 0
        assert event["trail_preservation_after"] is False
    print("aemeath_seraphic_duet_trail_multiplier_smoke_test ok")


if __name__ == "__main__":
    main()
