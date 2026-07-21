from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lynae_polychrome_leap_stage2_frame1_resource_timing_v124_smoke_test import ready_stage_2


def main() -> None:
    sim = ready_stage_2()
    assert sim.execute_action("lynae_polychrome_leap")
    stage_2 = sim.timeline[-1]
    source_id = stage_2.action_instance_id
    assert sim.execute_action("lynae_polychrome_leap")
    packets = [
        event for event in sim.state.scheduled_packet_event_log
        if event.get("action_instance_id") == source_id and event.get("packet_group_id") == "tune_rupture_packet_family"
    ]
    assert len(packets) == 6
    assert all(event["owner_character_id"] == "lynae" for event in packets)
    assert all(event["source_action_id"] == "lynae_polychrome_leap_stage_2" for event in packets)
    assert all(event["damage_applied"] > 0 for event in packets)
    assert len(stage_2.hit_details) == 0 and stage_2.direct_action_damage == 0.0
    source_damage = sum(event["damage_applied"] for event in packets)
    assert math.isclose(stage_2.scheduled_damage, source_damage, abs_tol=1e-9)
    assert sim.timeline[-1].scheduled_damage == 0.0
    assert math.isclose(sum(item.damage for item in sim.timeline), sim.state.total_damage, abs_tol=1e-6)
    print("lynae_polychrome_leap_stage2_source_attribution_no_duplicate_v124_smoke_test ok")


if __name__ == "__main__":
    main()
