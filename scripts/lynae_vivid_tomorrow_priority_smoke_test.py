from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_lynae_enabled_test_party"
VIVID_ID = "lynae_to_a_vivid_tomorrow"


def lynae_state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["lynae"]


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID, initial_active_character="lynae")
    state = lynae_state(sim)

    state["to_vivid_tomorrow_window_remaining"] = 8.0
    state["kaleidoscopic_parade_remaining"] = 0.0
    before = copy.deepcopy(state)
    assert sim.resolve_action_id("lynae_basic_attack") == VIVID_ID
    assert state == before

    state["to_vivid_tomorrow_window_remaining"] = 8.0
    state["kaleidoscopic_parade_remaining"] = 15.0
    state["kaleidoscopic_combo_stage"] = 2
    before = copy.deepcopy(state)
    assert sim.resolve_action_id("lynae_basic_attack") == VIVID_ID
    assert sim.resolve_action_id("lynae_basic_attack") != "lynae_kaleidoscopic_basic_stage_2"
    assert state == before

    assert sim.execute_action("lynae_basic_attack")
    row = sim.timeline[-1]
    assert row.resolved_action_id == VIVID_ID
    assert lynae_state(sim)["to_vivid_tomorrow_window_remaining"] == 0.0
    assert sim.resolve_action_id("lynae_basic_attack") == "lynae_kaleidoscopic_basic_stage_2"

    state = lynae_state(sim)
    state["to_vivid_tomorrow_window_remaining"] = 0.0
    state["kaleidoscopic_parade_remaining"] = 0.0
    assert sim.resolve_action_id("lynae_basic_attack") != VIVID_ID

    print("lynae_vivid_tomorrow_priority_smoke_test ok")


if __name__ == "__main__":
    main()
