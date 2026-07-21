from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lynae_polychrome_leap_stage2_frame1_resource_timing_v124_smoke_test import ready_stage_2


def main() -> None:
    sim = ready_stage_2()
    assert sim.execute_action("lynae_polychrome_leap")
    stage_2 = sim.timeline[-1]
    assert sim.execute_action("lynae_polychrome_leap")
    stage_3 = sim.timeline[-1]
    stage_2_events = [
        event for event in sim.state.chronological_event_log
        if event.get("source_action_id") == "lynae_polychrome_leap_stage_2" and event.get("packet_group_id")
    ]
    packet_5 = next(event for event in stage_2_events if event["packet_occurrence_index"] == 5)
    packet_6 = next(event for event in stage_2_events if event["packet_occurrence_index"] == 6)
    stage_3_start = next(
        event for event in sim.state.chronological_event_log
        if event.get("event_type") == "action_start" and event.get("source_action_id") == "lynae_polychrome_leap_stage_3"
    )
    assert stage_3.time_start == stage_2.time_start + 36 / 60
    assert packet_5["event_sequence"] < stage_3_start["event_sequence"]
    assert packet_6["event_sequence"] > stage_3_start["event_sequence"]
    assert packet_6["scheduled_wall_time"] == stage_2.time_start + 42 / 60
    assert packet_6["processed_wall_time"] == packet_6["scheduled_wall_time"]
    assert stage_3.scheduled_damage == 0.0
    print("lynae_polychrome_leap_stage2_stage3_overlap_v124_smoke_test ok")


if __name__ == "__main__":
    main()
