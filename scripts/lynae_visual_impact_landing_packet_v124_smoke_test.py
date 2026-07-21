from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.lynae_polychrome_leap_stage2_frame1_resource_timing_v124_smoke_test import ready_stage_2


def visual_ready(mode: str = "tune_rupture"):
    sim = ready_stage_2()
    assert sim.execute_action("lynae_polychrome_leap")
    assert sim.execute_action("lynae_polychrome_leap")
    sim.state.character_mechanics_state["lynae"]["lynae_resonance_mode"] = mode
    return sim


def main() -> None:
    for mode, group, frame_ref, damage_ref, control in (
        ("tune_rupture", "tune_rupture_landing", "A2682:AT2682", "dmg!A2464:DF2464", 53),
        ("tune_strain", "tune_strain_landing", "A2681:AT2681", "dmg!A2465:DF2465", 59),
    ):
        sim = visual_ready(mode); assert sim.execute_action("lynae_visual_impact")
        row = sim.timeline[-1]
        event = next(item for item in sim.state.chronological_event_log if item.get("source_action_id") == "lynae_visual_impact" and item.get("packet_group_id"))
        assert event["packet_group_id"] == group and event["processed_wall_time"] == event["scheduled_wall_time"] == row.time_start + 45 / 60
        packet = next(item for item in sim.state.scheduled_packet_instances if item.packet_instance_id == event["packet_instance_id"])
        assert any(frame_ref in ref for ref in packet.source_refs) and any(damage_ref in ref for ref in packet.source_refs)
        assert row.time_end == row.time_start + control / 60
    print("lynae_visual_impact_landing_packet_v124_smoke_test ok")


if __name__ == "__main__": main()
