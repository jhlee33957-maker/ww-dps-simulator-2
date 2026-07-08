from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


BASIC_STAGE_IDS = [
    "lynae_basic_stage_1",
    "lynae_basic_stage_2",
    "lynae_basic_stage_3",
    "lynae_kaleidoscopic_basic_stage_1",
    "lynae_kaleidoscopic_basic_stage_2",
    "lynae_kaleidoscopic_basic_stage_3",
    "lynae_kaleidoscopic_basic_stage_4",
    "lynae_kaleidoscopic_basic_stage_5",
]
KP_SEQUENCE = [
    "lynae_kaleidoscopic_basic_stage_1",
    "lynae_kaleidoscopic_basic_stage_2",
    "lynae_kaleidoscopic_basic_stage_3",
    "lynae_kaleidoscopic_basic_stage_4",
    "lynae_kaleidoscopic_basic_stage_5",
    "lynae_kaleidoscopic_basic_stage_1",
    "lynae_kaleidoscopic_basic_stage_2",
    "lynae_kaleidoscopic_basic_stage_3",
]


def main() -> None:
    actions = {action["id"]: action for action in json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))}
    for action_id in BASIC_STAGE_IDS:
        action = actions[action_id]
        assert action["cooldown"] == 0.0
        assert action.get("cooldown_group") is None

    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    sim.state.character_mechanics_state["lynae"]["overflow"] = 120.0
    assert sim.execute_action("lynae_spark_collision")

    seen = []
    for expected_action_id in KP_SEQUENCE:
        assert "lynae_basic_attack" in sim.valid_action_ids()
        assert sim.execute_action("lynae_basic_attack")
        seen.append(sim.state.action_log[-1]["resolved_action_id"])
        assert sim.state.action_log[-1]["resolved_action_id"] == expected_action_id

    assert seen == KP_SEQUENCE
    assert sim.state.cooldowns.get("lynae_kaleidoscopic_basic_stage_3", 0.0) <= 0.0

    print("lynae_kp_basic_no_cooldown_regression_smoke_test ok")


if __name__ == "__main__":
    main()
