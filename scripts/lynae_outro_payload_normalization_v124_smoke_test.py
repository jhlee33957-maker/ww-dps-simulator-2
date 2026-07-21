from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.action_timing_contract import load_action_timing_contracts
from scripts.lynae_real_cycle_concerto_smoke_test import LYNAE_SEQUENCE, MORNYE_OPENER, PARTY_ID
from simulator.simulation import Simulation


def main() -> None:
    contract = load_action_timing_contracts(ROOT / "data")["lynae_outro_lets_hit_the_road"]
    first, second = contract.scheduled_packet_groups
    raw_total = sum(group.damage_payload["source_raw_multiplier_total"] for group in (first, second))
    executable_total = sum(group.damage_payload["executable_multiplier_total"] for group in (first, second))
    assert math.isclose(raw_total, 1.001, abs_tol=1e-12)
    for group in (first, second):
        assert math.isclose(group.damage_payload["source_raw_multiplier_per_packet"], 0.0455, abs_tol=1e-12)
        assert math.isclose(group.damage_payload["normalization_factor"], 1 / 1.001, abs_tol=1e-12)
        assert math.isclose(group.damage_payload["executable_multiplier_per_packet"], 1 / 22, abs_tol=1e-12)
        assert group.resource_payload["off_tune_total"] == 0
        assert group.resource_payload["resonance_energy_total"] == 0
        assert group.resource_payload["concerto_total"] == 0
    assert math.isclose(first.damage_payload["executable_multiplier_total"], 12 / 22, abs_tol=1e-12)
    assert math.isclose(second.damage_payload["executable_multiplier_total"], 10 / 22, abs_tol=1e-12)
    assert math.isclose(executable_total, 1.0, abs_tol=1e-12)
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID, initial_active_character="mornye")
    for action_id in MORNYE_OPENER:
        assert sim.execute_action(action_id)
    assert sim.execute_action("swap_to_lynae")
    for action_id, _ in LYNAE_SEQUENCE:
        assert sim.execute_action(action_id)
    assert sim.execute_action("swap_to_aemeath")
    source_id = sim.timeline[-1].outgoing_scheduled_action_instance_id
    for _ in range(3):
        assert sim.execute_action("aemeath_basic_attack")
    events = [event for event in sim.state.scheduled_packet_event_log if event.get("action_instance_id") == source_id]
    assert len(events) == 22
    assert all(len(event["hit_details"]) == 1 for event in events)
    assert all(math.isclose(event["hit_details"][0]["base_coefficient"], 1 / 22, abs_tol=1e-12) for event in events)
    assert math.isclose(sum(event["hit_details"][0]["base_coefficient"] for event in events), 1.0, abs_tol=1e-12)
    print("lynae_outro_payload_normalization_v124_smoke_test ok")


if __name__ == "__main__":
    main()
