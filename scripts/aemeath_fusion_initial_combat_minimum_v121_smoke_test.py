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
    assert state["fusion_effect_stacks"] == 1 and state["fusion_trail_stacks"] == 0
    assert state["fusion_application_last_trigger_time"] == {}
    event = state["fusion_trail_event_log"][-1]
    assert event["event_type"] == "fusion_effect_in_combat_minimum"
    assert event["base_trajectory_gain"] == 0 and event["s6_post_application_gain"] == 0
    print("aemeath_fusion_initial_combat_minimum_v121_smoke_test ok")


if __name__ == "__main__":
    main()
