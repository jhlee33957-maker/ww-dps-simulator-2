from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    assert sim.execute_action("lynae_resonance_liberation")
    assert sim.state.character_mechanics_state["lynae"]["to_vivid_tomorrow_window_remaining"] > 0.0
    assert sim.resolve_action_id("lynae_basic_attack") == "lynae_to_a_vivid_tomorrow"
    assert sim.execute_action("lynae_basic_attack")
    row = sim.state.action_log[-1]
    assert row["resolved_action_id"] == "lynae_to_a_vivid_tomorrow"
    assert row["lynae_to_vivid_tomorrow_window_remaining"] == 0.0
    print("lynae_liberation_vivid_tomorrow_smoke_test ok")


if __name__ == "__main__":
    main()
