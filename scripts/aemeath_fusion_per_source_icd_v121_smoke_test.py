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
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert sim.last_action_result.mechanic_event_cooldown_blocked is True
    assert state["fusion_effect_stacks"] == 2 and state["fusion_trail_stacks"] == 2
    assert sim.execute_action("aemeath_basic_form_stage_4")
    assert state["fusion_effect_stacks"] == 3 and state["fusion_trail_stacks"] == 4
    cooldowns = state["fusion_application_last_trigger_time"]
    assert set(cooldowns) == {
        "aemeath:aemeath_basic_form_stage_3",
        "aemeath:aemeath_basic_form_stage_4",
    }
    print("aemeath_fusion_per_source_icd_v121_smoke_test ok")


if __name__ == "__main__":
    main()
