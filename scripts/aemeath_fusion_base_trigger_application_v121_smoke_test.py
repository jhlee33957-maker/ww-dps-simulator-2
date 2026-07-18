from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    for action_id in (
        "aemeath_basic_form_stage_3",
        "aemeath_basic_form_stage_4",
        "aemeath_mech_basic_stage_3",
        "aemeath_mech_basic_stage_4",
    ):
        sim = make_account_sim("aemeath", aemeath_resonance_mode="fusion_burst")
        state = sim.state.character_mechanics_state["aemeath"]
        assert sim.execute_action(action_id), action_id
        assert sim.last_action_result.emitted_mechanic_event_tags == ["fusion_burst"]
        assert state["fusion_effect_stacks"] == 2
        assert state["fusion_trail_stacks"] == 2
        event = state["fusion_trail_event_log"][-1]
        assert event["source_action_id"] == action_id
        assert event["base_trajectory_gain"] == 1
        assert event["s6_post_application_gain"] == 1

    tune = make_account_sim("aemeath", aemeath_resonance_mode="tune_rupture")
    assert tune.execute_action("aemeath_basic_form_stage_3")
    assert tune.state.character_mechanics_state["aemeath"]["fusion_effect_stacks"] == 0
    assert tune.state.character_mechanics_state["aemeath"]["fusion_trail_stacks"] == 0
    print("aemeath_fusion_base_trigger_application_v121_smoke_test ok")


if __name__ == "__main__":
    main()
