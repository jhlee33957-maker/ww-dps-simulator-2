from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    state = sim.state.character_mechanics_state["lynae"]
    assert not sim.is_action_available(sim.actions["lynae_spark_collision"])
    state["overflow"] = 120.0
    assert sim.resolve_action_id("lynae_spark_collision") == "lynae_spark_collision_lv3"
    assert sim.is_action_available(sim.actions["lynae_spark_collision"])
    assert sim.execute_action("lynae_spark_collision")
    row = sim.state.action_log[-1]
    assert row["resolved_action_id"] == "lynae_spark_collision_lv3"
    assert row["lynae_overflow"] == 0.0
    assert row["lynae_lumiflow"] == 120.0
    assert row["lynae_kaleidoscopic_parade_remaining"] > 0.0
    assert row["lynae_optical_sampling_stage_active"] is False
    print("lynae_spark_collision_kaleidoscopic_entry_smoke_test ok")


if __name__ == "__main__":
    main()
