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
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert state["fusion_effect_stacks"] == 2 and state["fusion_trail_stacks"] == 2
    assert [event["event_type"] for event in state["fusion_trail_event_log"][:2]] == [
        "fusion_effect_in_combat_minimum", "fusion_effect_application"
    ]
    print("aemeath_fusion_first_action_order_v121_smoke_test ok")


if __name__ == "__main__":
    main()
