from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import ACCOUNT_SCOPE_ID
from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(
        ROOT / "data",
        selected_character_ids=["aemeath"],
        initial_active_character="aemeath",
        build_profile_overrides={"aemeath": "aemeath_account_actual_01"},
        account_simulation_scope=ACCOUNT_SCOPE_ID,
        precombat_elapsed_seconds=5.0,
    )
    sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.enemy_mistune_active = True
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0
    assert sim.execute_action("aemeath_tune_break")
    detail = next(hit for hit in sim.last_action_result.tune_response_hit_details if hit["tune_response_id"] == "aemeath_starburst")
    assert detail["crit_rate_after_override"] == 0.80
    assert detail["crit_damage_after_override"] == 2.75
    assert detail["expected_crit_multiplier"] == 2.40
    assert detail["damage"] == detail["damage_before_account_fixed_crit"] * 2.40
    assert sim.last_action_result.total_action_damage == sum(hit["damage"] for hit in sim.last_action_result.hit_details)
    print("aemeath_s6_starburst_fixed_crit_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
