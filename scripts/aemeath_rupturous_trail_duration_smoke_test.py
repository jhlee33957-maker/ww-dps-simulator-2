from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    sim.state.rupturous_trail_stacks = 20
    sim.state.rupturous_trail_remaining = 30.0
    sim._advance_tune_break_runtime(action_elapsed=30.0, combat_elapsed=12.5)
    assert sim.state.rupturous_trail_stacks == 20
    assert sim.state.rupturous_trail_remaining == 17.5
    sim._advance_tune_break_runtime(action_elapsed=0.0, combat_elapsed=17.5)
    assert sim.state.rupturous_trail_stacks == 0
    assert sim.state.rupturous_trail_remaining == 0.0
    print("aemeath_rupturous_trail_duration_smoke_test ok")


if __name__ == "__main__":
    main()
