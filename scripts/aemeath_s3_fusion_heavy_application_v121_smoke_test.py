from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import make_account_sim, ready_aemeath_charged_ii


def main() -> None:
    sim = make_account_sim("aemeath", aemeath_resonance_mode="fusion_burst")
    ready_aemeath_charged_ii(sim)
    assert sim.execute_action("aemeath_heavy_aemeath_charged_2")
    state = sim.state.character_mechanics_state["aemeath"]
    account = sim.state.character_mechanics_state["_account_constellation"]
    assert state["fusion_effect_stacks"] == 2 and state["fusion_trail_stacks"] == 2
    assert account["aemeath_s3_fusion_contributors"] == ["aemeath"]

    for action_id, instant_response in (
        ("aemeath_heavy_aemeath_charged_1", True),
        ("aemeath_heavy_aemeath_charged_2", False),
    ):
        negative = make_account_sim("aemeath", aemeath_resonance_mode="fusion_burst")
        negative_data = negative.state.character_mechanics_state["aemeath"]
        negative_data["instant_response"] = instant_response
        if not instant_response:
            negative_data["heavenfall_unbound_remaining"] = 0.0
            negative_data["resonance_rate"] = 0.0
        assert negative.execute_action(action_id)
        negative_state = negative.state.character_mechanics_state["aemeath"]
        assert negative_state["fusion_effect_stacks"] == 1
        assert negative_state["fusion_trail_stacks"] == 0
    print("aemeath_s3_fusion_heavy_application_v121_smoke_test ok")


if __name__ == "__main__":
    main()
