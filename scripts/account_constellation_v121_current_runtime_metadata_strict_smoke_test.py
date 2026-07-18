from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath", aemeath_resonance_mode="fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert sim.execute_action("aemeath_sync_strike_armament_merge")
    assert any(hit.get("generated_damage_packet_id") == "aemeath_seraphic_duet_fusion_burst_settlement" for hit in sim.last_action_result.hit_details)
    unsupported = set(sim.summary().unsupported_aemeath_followup_mechanics)
    assert unsupported == {
        "stardust_resonance_extra_effects", "aemeath_s1_kill_trajectory_transfer", "aemeath_s2_kill_triggered_detonation",
        "aemeath_s5_all_effects", "enemy_movement_or_pull", "player_survival_effects", "multi_target_trajectory_tracking",
    }
    assert not any("fusion" in value or "rupturous_trail" in value for value in unsupported)
    print("account_constellation_v121_current_runtime_metadata_strict_smoke_test ok")


if __name__ == "__main__":
    main()
