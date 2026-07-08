from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


ACTION_ID = "lynae_iridescent_splash"


def main() -> None:
    actions = {action["id"]: action for action in json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))}
    iridescent = actions[ACTION_ID]
    assert iridescent["policy_selectable"] is True
    assert iridescent["cooldown"] == 0.0
    assert iridescent.get("cooldown_group") is None

    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    sim.state.character_mechanics_state["lynae"]["overflow"] = 120.0
    assert sim.execute_action("lynae_spark_collision")

    state = sim.state.character_mechanics_state["lynae"]
    state["true_color"] = 3.0
    state["visual_impact_cooldown_remaining"] = 10.0

    assert ACTION_ID in sim.policy_actions
    assert ACTION_ID in sim.valid_action_ids()
    assert sim.execute_action(ACTION_ID)

    row = sim.state.action_log[-1]
    state = sim.state.character_mechanics_state["lynae"]
    assert row["selected_action_id"] == ACTION_ID
    assert row["resolved_action_id"] == ACTION_ID
    assert state["true_color"] == 0.0
    assert row["lynae_photocromic_flux_applied"] is True
    assert state["photocromic_flux_active"] is True
    assert ACTION_ID not in sim.valid_action_ids()
    assert sim.execute_action(ACTION_ID) is False

    print("lynae_iridescent_policy_availability_smoke_test ok")


if __name__ == "__main__":
    main()
