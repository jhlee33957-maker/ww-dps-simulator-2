from __future__ import annotations

import math
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
    policy_actions_before = len(sim.state.action_log)
    assert sim.execute_action("swap_to_aemeath")
    transition = sim.timeline[-1]
    source_id = transition.outgoing_scheduled_action_instance_id
    assert len(sim.state.action_log) == policy_actions_before + 1
    assert transition.scheduled_damage == 0.0
    assert transition.outgoing_scheduled_source_summary["policy_step"] is False
    assert transition.outgoing_scheduled_source_summary["auxiliary_transition_source_action"] is True
    for _ in range(3):
        assert sim.execute_action("aemeath_basic_attack")
    events = [event for event in sim.state.scheduled_packet_event_log if event.get("action_instance_id") == source_id]
    assert len(events) == 22
    assert all(event["owner_character_id"] == "lynae" for event in events)
    assert all(event["source_action_id"] == "lynae_outro_lets_hit_the_road" for event in events)
    assert all(event["action_instance_id"] == source_id for event in events)
    assert all(event["processed_wall_time"] == event["scheduled_wall_time"] for event in events)
    assert all(event["transition_source_damage_enabled"] is True for event in events)
    assert all(len(event["hit_details"]) == 1 for event in events)
    assert all(event["damage_applied"] > 0 and event["normal_damage"] > 0 for event in events)
    source_damage = sum(float(event["damage_applied"]) for event in events)
    summary = next(item for item in sim.timeline if item.outgoing_scheduled_action_instance_id == source_id).outgoing_scheduled_source_summary
    assert summary["scheduled_packet_count"] == 22
    assert math.isclose(summary["scheduled_damage"], source_damage, abs_tol=1e-9)
    assert source_damage > 0 and summary["scheduled_damage"] > 0
    assert transition.scheduled_damage == 0.0
    assert math.isclose(transition.total_action_damage, transition.direct_action_damage, abs_tol=1e-9)
    assert all(hit["static_mist_incoming_atk_buff_active"] is False for event in events for hit in event["hit_details"])
    assert all(hit["pact_neonlight_incoming_atk_buff_active"] is False for event in events for hit in event["hit_details"])
    ordinary_timeline_damage = sum(item.damage for item in sim.timeline)
    auxiliary_damage = sum(
        item.outgoing_scheduled_source_summary.get("scheduled_damage", 0.0)
        for item in sim.timeline
        if item.outgoing_scheduled_action_instance_id
    )
    assert math.isclose(ordinary_timeline_damage + auxiliary_damage, sim.state.total_damage, abs_tol=1e-6)
    assert not any(hit.get("name") == "lynae_outro_lets_hit_the_road" for hit in transition.hit_details)
    print("lynae_outro_source_attribution_no_serialization_v124_smoke_test ok")


if __name__ == "__main__":
    main()
