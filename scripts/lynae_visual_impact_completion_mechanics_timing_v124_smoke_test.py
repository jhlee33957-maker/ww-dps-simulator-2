from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.lynae_visual_impact_landing_packet_v124_smoke_test import visual_ready


def main() -> None:
    for mode, control in (("tune_rupture", 53), ("tune_strain", 59)):
        sim = visual_ready(mode); before = sim.state.character_mechanics_state["lynae"]["true_color"]
        assert sim.execute_action("lynae_visual_impact"); row = sim.timeline[-1]
        landing = next(item for item in sim.state.chronological_event_log if item.get("source_action_id") == "lynae_visual_impact" and item.get("packet_group_id"))
        end = next(item for item in sim.state.chronological_event_log if item.get("source_action_id") == "lynae_visual_impact" and item.get("event_type") == "action_end")
        assert landing["event_sequence"] < end["event_sequence"] and row.combat_time_end == row.combat_time_start + control / 60
        assert sim.state.character_mechanics_state["lynae"]["true_color"] == 0.0 and before >= 0.0
        assert sim.state.character_mechanics_state["lynae"]["visual_impact_cooldown_remaining"] == 25.0
        effect = sim.scheduled_effect_by_instance_id(sim.LYNAE_SPRAY_PAINT_INSTANCE_ID)
        assert effect is not None and effect.activation_combat_time == row.combat_time_end
    print("lynae_visual_impact_completion_mechanics_timing_v124_smoke_test ok")


if __name__ == "__main__": main()
