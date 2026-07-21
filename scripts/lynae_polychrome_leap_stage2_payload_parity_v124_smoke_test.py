from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.action_timing_contract import load_action_timing_contracts, start_ongoing_action
from simulator.simulation import Simulation


def main() -> None:
    contract = load_action_timing_contracts(ROOT / "data")["lynae_polychrome_leap_stage_2"]
    for mode, expected_group in (("tune_rupture", "tune_rupture_packet_family"), ("tune_strain", "tune_strain_packet_family")):
        sim = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party", initial_active_character="lynae")
        sim.state.character_mechanics_state["lynae"]["lynae_resonance_mode"] = mode
        instance = start_ongoing_action(sim.state, sim.actions[contract.action_id], contract)
        sim.state.character_mechanics_state["lynae"]["lynae_resonance_mode"] = (
            "tune_strain" if mode == "tune_rupture" else "tune_rupture"
        )
        packets = [packet for packet in sim.state.scheduled_packet_instances if packet.action_instance_id == instance.action_instance_id]
        damage_packets = [packet for packet in packets if packet.packet_group_id == expected_group]
        assert len(damage_packets) == 6
        assert {packet.packet_group_id for packet in packets} == {"frame_1_true_color_lumiflow", expected_group}
        assert all(math.isclose(packet.damage_payload["damage_multiplier"], 0.169, abs_tol=1e-12) for packet in damage_packets)
        assert all(math.isclose(packet.resource_payload["off_tune_value"], 8.0, abs_tol=1e-12) for packet in damage_packets)
        assert all(math.isclose(packet.resource_payload["resonance_energy_gain"], 0.38, abs_tol=1e-12) for packet in damage_packets)
        assert all(math.isclose(packet.resource_payload["concerto_energy_gain"], 0.9, abs_tol=1e-12) for packet in damage_packets)
        assert math.isclose(sum(packet.damage_payload["damage_multiplier"] for packet in damage_packets), 1.014, abs_tol=1e-12)
        assert math.isclose(sum(packet.resource_payload["off_tune_value"] for packet in damage_packets), 48.0, abs_tol=1e-12)
        assert math.isclose(sum(packet.resource_payload["resonance_energy_gain"] for packet in damage_packets), 2.28, abs_tol=1e-12)
        assert math.isclose(sum(packet.resource_payload["concerto_energy_gain"] for packet in damage_packets), 5.4, abs_tol=1e-12)
    print("lynae_polychrome_leap_stage2_payload_parity_v124_smoke_test ok")


if __name__ == "__main__":
    main()
