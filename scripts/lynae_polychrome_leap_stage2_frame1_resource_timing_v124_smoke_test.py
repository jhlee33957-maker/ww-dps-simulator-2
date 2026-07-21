from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lynae_real_cycle_concerto_smoke_test import MORNYE_OPENER, PARTY_ID
from simulator.simulation import Simulation


def ready_stage_2() -> Simulation:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID, initial_active_character="mornye")
    for action_id in MORNYE_OPENER:
        assert sim.execute_action(action_id), action_id
    assert sim.execute_action("swap_to_lynae")
    assert sim.execute_action("lynae_resonance_skill")
    assert sim.execute_action("lynae_spark_collision")
    assert sim.execute_action("lynae_polychrome_leap")
    return sim


def main() -> None:
    sim = ready_stage_2()
    before = dict(sim.state.character_mechanics_state["lynae"])
    assert sim.execute_action("lynae_polychrome_leap")
    events = [
        event for event in sim.state.scheduled_packet_event_log
        if event.get("source_action_id") == "lynae_polychrome_leap_stage_2"
        and event.get("resource_event_only")
    ]
    assert len(events) == 1
    event = events[0]
    assert round((event["scheduled_wall_time"] - sim.timeline[-1].time_start) * 60) == 1
    assert event["true_color_before"] == before["true_color"]
    assert event["true_color_applied"] == 1
    assert event["lumiflow_before"] == before["lumiflow"]
    assert event["lumiflow_applied"] == -40
    state = sim.state.character_mechanics_state["lynae"]
    assert state["true_color"] == before["true_color"] + 1
    assert state["lumiflow"] == before["lumiflow"] - 40
    assert event["processed_wall_time"] == event["scheduled_wall_time"]
    print("lynae_polychrome_leap_stage2_frame1_resource_timing_v124_smoke_test ok")


if __name__ == "__main__":
    main()
