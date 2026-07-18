from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import ACCOUNT_BUILD_OVERRIDES, PARTY
from simulator.account_constellation_effects import ACCOUNT_SCOPE_ID
from simulator.simulation import Simulation


def main() -> None:
    simulation = Simulation.from_json(
        ROOT / "data",
        selected_character_ids=PARTY,
        initial_active_character="aemeath",
        build_profile_overrides=ACCOUNT_BUILD_OVERRIDES,
        account_simulation_scope=ACCOUNT_SCOPE_ID,
        precombat_elapsed_seconds=5.0,
    )
    simulation.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "fusion_burst"
    state = simulation.state.character_mechanics_state["aemeath"]
    state.update({"fusion_trail_stacks": 10, "fusion_trail_remaining": 30.0, "fusion_effect_stacks": 1, "fusion_effect_remaining": 15.0})
    assert simulation.execute_action("aemeath_sync_strike_armament_merge")
    hit = next(item for item in simulation.last_action_result.hit_details if item.get("generated_damage_packet_id") == "aemeath_seraphic_duet_fusion_burst_settlement")
    assert hit["damage"] > 0.0
    assert hit["fusion_effect_final_damage_multiplier"] == 6.5
    print("aemeath_s2_fusion_packet_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
