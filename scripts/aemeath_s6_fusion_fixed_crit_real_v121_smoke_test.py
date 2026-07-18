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
    hit = next(hit for hit in sim.last_action_result.hit_details if hit.get("generated_damage_packet_id") == "aemeath_seraphic_duet_fusion_burst_settlement")
    assert hit["crit_rate_after_override"] == 0.80
    assert hit["crit_damage_after_override"] == 2.75
    assert hit["expected_crit_multiplier"] == 2.40
    assert hit["damage"] == hit["damage_before_account_fixed_crit"] * 2.40
    print("aemeath_s6_fusion_fixed_crit_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
