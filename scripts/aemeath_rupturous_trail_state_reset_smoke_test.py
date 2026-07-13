from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    sim.state.rupturous_trail_stacks = 30
    sim.state.rupturous_trail_remaining = 30.0
    fresh = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    assert fresh.state.rupturous_trail_stacks == 0
    assert fresh.state.rupturous_trail_remaining == 0.0
    assert fresh.state.rupturous_trail_event_log == []
    print("aemeath_rupturous_trail_state_reset_smoke_test ok")


if __name__ == "__main__":
    main()
