from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    assert sim.execute_action("lynae_basic_attack")
    assert sim.state.action_log[-1]["resolved_action_id"] == "lynae_basic_stage_1"
    assert sim.state.character_mechanics_state["lynae"]["overflow"] == 12.0
    assert sim.execute_action("lynae_basic_attack")
    assert sim.state.action_log[-1]["resolved_action_id"] == "lynae_basic_stage_2"
    assert sim.state.character_mechanics_state["lynae"]["overflow"] == 33.0
    assert sim.execute_action("lynae_basic_attack")
    assert sim.state.action_log[-1]["resolved_action_id"] == "lynae_basic_stage_3"
    assert sim.state.character_mechanics_state["lynae"]["overflow"] == 50.0
    assert sim.execute_action("lynae_resonance_skill")
    assert sim.state.action_log[-1]["resolved_action_id"] == "lynae_resonance_skill_palette"
    assert sim.state.character_mechanics_state["lynae"]["overflow"] == 75.0
    print("lynae_resource_flow_smoke_test ok")


if __name__ == "__main__":
    main()
