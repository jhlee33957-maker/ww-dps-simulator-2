from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath", aemeath_resonance_mode="fusion_burst")
    state = sim.state.character_mechanics_state["aemeath"]
    assert sim.execute_action("aemeath_basic_form_stage_1")
    assert state["fusion_effect_stacks"] == 1
    assert state["fusion_trail_stacks"] == 0
    assert state["fusion_effect_remaining"] == 0.0
    minimum = state["fusion_trail_event_log"][-1]
    assert minimum["event_type"] == "fusion_effect_in_combat_minimum"
    assert minimum["fusion_effect_duration_seconds"] is None
    state["fusion_effect_stacks"] = 0
    assert sim.execute_action("aemeath_basic_form_stage_1")
    assert state["fusion_effect_stacks"] == 1
    assert state["fusion_trail_stacks"] == 0
    print("aemeath_fusion_in_combat_minimum_effect_v121_smoke_test ok")


if __name__ == "__main__":
    main()
