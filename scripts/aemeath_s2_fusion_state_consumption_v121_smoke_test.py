from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import make_account_sim


def _settle(stacks: int, *, preserve: bool) -> tuple[dict, object]:
    sim = make_account_sim("aemeath", aemeath_resonance_mode="fusion_burst")
    state = sim.state.character_mechanics_state["aemeath"]
    state.update({"fusion_trail_stacks": stacks, "fusion_trail_remaining": 30.0, "fusion_effect_stacks": 1, "fusion_effect_remaining": 15.0, "trail_no_cost_remaining": 30.0 if preserve else 0.0})
    assert sim.execute_action("aemeath_sync_strike_call_of_dawn")
    return state, sim.last_action_result


def main() -> None:
    preserved, _result = _settle(10, preserve=True)
    assert preserved["last_seraphic_duet_consumed_fusion_trail_stacks"] == 0
    assert preserved["trail_no_cost_remaining"] == 0.0
    assert preserved["fusion_trail_stacks"] == 12
    for stacks in (1, 10, 30, 60):
        state, result = _settle(stacks, preserve=False)
        hit = next(hit for hit in result.hit_details if hit.get("generated_damage_packet_id") == "aemeath_seraphic_duet_fusion_burst_settlement")
        assert abs(hit["fusion_effect_final_damage_multiplier"] - (5.0 + 0.15 * stacks)) < 1e-12
        assert state["last_seraphic_duet_consumed_fusion_trail_stacks"] == stacks
        assert state["fusion_effect_stacks"] > 0
    print("aemeath_s2_fusion_state_consumption_v121_smoke_test ok")


if __name__ == "__main__":
    main()
