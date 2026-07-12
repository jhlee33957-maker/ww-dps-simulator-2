from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def ready(sim: Simulation, state: str = "tune_rupture_shifting") -> None:
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = state
    sim.state.target_tune_shift_remaining = 8.0 if state == "tune_rupture_shifting" else 30.0


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    ready(sim)
    assert sim.execute_action("mornye_tune_break")
    row = sim.timeline[-1]
    events = row.aemeath_rupturous_trail_gain_events
    assert [event["stacks_before"] for event in events] == [0, 10, 20]
    assert [event["requested_gain"] for event in events] == [10, 10, 10]
    assert [event["applied_gain"] for event in events] == [10, 10, 10]
    assert [event["stacks_after"] for event in events] == [10, 20, 30]
    assert all(event["event_type"] == "rupturous_trail_gain" for event in events)
    assert all(event["response_source_character_id"] for event in events)
    assert all(event["response_action_id"] for event in events)
    assert [event["remaining_after"] for event in events] == [30.0, 30.0, 30.0]
    assert sim.state.rupturous_trail_stacks == 30
    assert sim.state.rupturous_trail_remaining == 30.0

    ready(sim)
    assert sim.execute_action("mornye_tune_break")
    blocked = sim.timeline[-1]
    assert blocked.tune_response_damage == 0.0
    assert blocked.aemeath_rupturous_trail_gain_events == []
    assert sim.state.rupturous_trail_stacks == 30

    strain = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    ready(strain, "tune_strain_shifting")
    assert strain.execute_action("mornye_tune_break")
    assert strain.timeline[-1].lynae_spectral_analysis_triggered is True
    assert strain.state.rupturous_trail_stacks == 0
    print("aemeath_rupturous_trail_response_gain_smoke_test ok")


if __name__ == "__main__":
    main()
