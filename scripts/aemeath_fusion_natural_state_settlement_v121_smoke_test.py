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
    assert state["fusion_effect_stacks"] == 1 and state["fusion_trail_stacks"] == 0
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert state["fusion_effect_stacks"] == 2 and state["fusion_trail_stacks"] == 2
    assert sim.execute_action("aemeath_sync_strike_armament_merge")
    result = sim.last_action_result
    hit = next(hit for hit in result.hit_details if hit.get("generated_damage_packet_id") == "aemeath_seraphic_duet_fusion_burst_settlement")
    assert hit["fusion_effect_multiplier"] == 6.9863
    assert hit["fusion_effect_final_damage_multiplier"] == 5.3
    assert hit["crit_rate_after_override"] == 0.80
    assert hit["crit_damage_after_override"] == 2.75
    assert hit["expected_crit_multiplier"] == 2.40
    assert state["last_seraphic_duet_consumed_fusion_trail_stacks"] == 2
    assert state["fusion_effect_stacks"] == 3
    assert state["fusion_trail_stacks"] == 2
    assert sum(item["damage"] for item in result.hit_details) == result.total_action_damage
    print("aemeath_fusion_natural_state_settlement_v121_smoke_test ok")


if __name__ == "__main__":
    main()
