from __future__ import annotations

from v124_timing_test_support import VIVID_ID, make_sim
from simulator.action_timing_contract import start_ongoing_action


def main() -> None:
    sim = make_sim("lynae")
    instance = start_ongoing_action(sim.state, sim.actions[VIVID_ID], sim.action_timing_contracts[VIVID_ID])
    packets = [packet for packet in sim.state.scheduled_packet_instances if packet.action_instance_id == instance.action_instance_id]
    assert len(packets) == 22
    assert {packet.packet_group_id for packet in packets} == {"row_2697_packet_family", "row_2698_packet_family"}
    assert all(packet.owner_character_id == "lynae" and packet.source_action_id == VIVID_ID for packet in packets)
    assert all(not packet.resolved and not packet.cancelled for packet in packets)
    assert all(not packet.damage_payload.get("placeholder") for packet in packets)
    first = [packet for packet in packets if packet.packet_group_id == "row_2697_packet_family"]
    second = [packet for packet in packets if packet.packet_group_id == "row_2698_packet_family"]
    assert len(first) == 12 and len(second) == 10
    assert all(packet.damage_payload["damage_multiplier"] == 0.0838 for packet in first)
    assert all(packet.damage_payload["damage_multiplier"] == 0.1005 for packet in second)
    assert sim.state.total_damage == 0.0
    print("scheduled_packet_placeholder_v124_smoke_test ok vivid_resolved_packets=22")


if __name__ == "__main__":
    main()
