from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    action = sim.actions["lynae_echo_hyvatia"]
    hits = action.effective_hits()
    assert len(hits) == 10
    assert all(abs(hit.damage_multiplier - 0.2736) < 1e-9 for hit in hits)
    assert abs(sum(hit.damage_multiplier for hit in hits) - 2.736) < 1e-9
    assert action.damage_element == "spectro"
    assert action.damage_bonus_category == "echo_ability"
    assert sim.execute_action("lynae_echo_hyvatia")
    assert sim.state.character_mechanics_state["lynae"]["hyvatia_outro_window_remaining"] > 0.0
    sim.state.concerto_energy["lynae"] = 100.0
    assert sim.execute_action("swap_to_aemeath")
    row = sim.state.action_log[-1]
    assert row["lynae_hyvatia_incoming_all_attribute_buff"] is True
    assert row["lynae_hyvatia_incoming_all_attribute_value"] == 0.10

    sim2 = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    assert sim2.execute_action("lynae_echo_hyvatia")
    sim2.state.character_mechanics_state["lynae"]["hyvatia_outro_window_remaining"] = 0.0
    sim2.state.concerto_energy["lynae"] = 100.0
    assert sim2.execute_action("swap_to_aemeath")
    assert sim2.state.action_log[-1]["lynae_hyvatia_incoming_all_attribute_buff"] is False
    print("hyvatia_echo_ability_smoke_test ok")


if __name__ == "__main__":
    main()
