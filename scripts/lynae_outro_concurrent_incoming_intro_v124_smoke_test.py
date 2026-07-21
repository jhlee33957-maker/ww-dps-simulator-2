from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lynae_real_cycle_concerto_smoke_test import LYNAE_SEQUENCE, MORNYE_OPENER, PARTY_ID
from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID, initial_active_character="mornye")
    for action_id in MORNYE_OPENER:
        assert sim.execute_action(action_id)
    assert sim.execute_action("swap_to_lynae")
    for action_id, _ in LYNAE_SEQUENCE:
        assert sim.execute_action(action_id)
    transition_wall_time = sim.state.current_time
    assert sim.execute_action("swap_to_aemeath")
    transition = sim.timeline[-1]
    source_id = transition.outgoing_scheduled_action_instance_id
    assert transition.resolved_action_id == "transition:aemeath_qte_intro_human"
    assert transition.action_time < 153 / 60
    assert transition.time_start == transition_wall_time
    assert transition.outgoing_scheduled_action_started is True
    assert transition.outgoing_scheduled_source_summary["start_wall_time"] == transition_wall_time
    assert transition.outgoing_scheduled_source_summary["start_combat_time"] == transition.combat_time_start
    assert transition.time_end < transition_wall_time + 181 / 60
    events = [event for event in sim.state.scheduled_packet_event_log if event.get("action_instance_id") == source_id]
    assert [round((event["scheduled_wall_time"] - transition_wall_time) * 60) for event in events] == [52, 58, 64, 70]
    assert all(event["processed_wall_time"] == event["scheduled_wall_time"] for event in events)
    assert all(event["transition_source_damage_enabled"] is True for event in events)
    assert all(event["damage_applied"] > 0 and event["normal_damage"] > 0 for event in events)
    assert all(len(event["hit_details"]) == 1 for event in events)
    intro_hit = next(
        event
        for event in sim.state.chronological_event_log
        if event["event_type"] == "action_hit" and event["source_action_id"] == "transition:aemeath_qte_intro_human"
    )
    assert [event["event_sequence"] for event in events] < [intro_hit["event_sequence"]] * len(events)
    for _ in range(3):
        assert sim.execute_action("aemeath_basic_attack")
    events = [event for event in sim.state.scheduled_packet_event_log if event.get("action_instance_id") == source_id]
    assert len(events) == 22
    assert all(event["processed_wall_time"] == event["scheduled_wall_time"] for event in events)
    print("lynae_outro_concurrent_incoming_intro_v124_smoke_test ok")


if __name__ == "__main__":
    main()
