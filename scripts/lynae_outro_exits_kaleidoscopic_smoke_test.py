from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    state = sim.state.character_mechanics_state["lynae"]
    state["overflow"] = 120.0
    assert sim.execute_action("lynae_spark_collision")
    state["true_color"] = 3.0
    sim.state.concerto_energy["lynae"] = 100.0
    assert sim.execute_action("swap_to_aemeath")
    row = sim.state.action_log[-1]
    assert row["outgoing_outro_applied"] is True
    assert row["lynae_kaleidoscopic_parade_remaining"] == 0.0
    assert row["lynae_lumiflow"] == 0.0
    assert row["lynae_true_color"] == 0.0
    assert state["optical_sampling_stage_active"] is True
    print("lynae_outro_exits_kaleidoscopic_smoke_test ok")


if __name__ == "__main__":
    main()
