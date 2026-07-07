from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    sim.state.character_mechanics_state["lynae"]["overflow"] = 120.0
    assert sim.execute_action("lynae_spark_collision")
    expected = [f"lynae_kaleidoscopic_basic_stage_{index}" for index in range(1, 6)]
    seen = []
    for _ in expected:
        assert sim.execute_action("lynae_basic_attack")
        seen.append(sim.state.action_log[-1]["resolved_action_id"])
    assert seen == expected
    assert sim.state.character_mechanics_state["lynae"]["kaleidoscopic_combo_stage"] == 1
    print("lynae_kaleidoscopic_combo_smoke_test ok")


if __name__ == "__main__":
    main()
