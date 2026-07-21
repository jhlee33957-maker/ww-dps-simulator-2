from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.lynae_polychrome_leap_stage2_frame1_resource_timing_v124_smoke_test import ready_stage_2


def main() -> None:
    sim = ready_stage_2()
    assert sim.execute_action("lynae_polychrome_leap")
    assert sim.execute_action("lynae_polychrome_leap")
    assert sim.state.character_mechanics_state["lynae"]["lynae_resonance_mode"] == "tune_rupture"
    assert sim.execute_action("lynae_visual_impact")
    row = sim.timeline[-1]
    assert row.action_time == row.effective_combat_time_cost == 53 / 60
    assert row.time_end == row.time_start + 53 / 60 and row.combat_time_end == row.combat_time_start + 53 / 60
    assert row.lynae_true_color == 0.0 and row.lynae_visual_impact_cooldown_remaining == 25.0
    assert row.lynae_visual_impact_tune_break_boost_buff_active and row.lynae_spray_paint_scheduled
    effect = sim.scheduled_effect_by_instance_id(sim.LYNAE_SPRAY_PAINT_INSTANCE_ID)
    assert effect is not None and effect.activation_combat_time == row.combat_time_end
    print("lynae_visual_impact_natural_route_v124_smoke_test ok")


if __name__ == "__main__": main()
