from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath", aemeath_resonance_mode="fusion_burst")
    state = sim.state.character_mechanics_state["aemeath"]
    state.update({"fusion_trail_stacks": 10, "fusion_trail_remaining": 30.0, "fusion_effect_stacks": 1, "fusion_effect_remaining": 15.0})
    assert sim.execute_action("aemeath_sync_strike_armament_merge")
    result = sim.last_action_result
    packet_hits = [hit for hit in result.hit_details if hit.get("generated_damage_packet_id") == "aemeath_seraphic_duet_fusion_burst_settlement"]
    assert len(packet_hits) == 1
    hit = packet_hits[0]
    assert hit["fusion_effect_multiplier"] == 6.9863
    assert hit["fusion_effect_final_damage_multiplier"] == 6.5
    assert hit["damage"] > 0.0
    assert result.total_action_damage == sum(hit["damage"] for hit in result.hit_details)
    assert state["last_seraphic_duet_consumed_fusion_trail_stacks"] == 10
    assert state["fusion_effect_stacks"] == 2
    assert state["fusion_trail_stacks"] == 2
    print("aemeath_s2_fusion_real_action_settlement_v121_smoke_test ok")


if __name__ == "__main__":
    main()
