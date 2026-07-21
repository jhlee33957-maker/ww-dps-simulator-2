from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.lynae_visual_impact_landing_packet_v124_smoke_test import visual_ready


def main() -> None:
    sim = visual_ready(); assert sim.execute_action("lynae_visual_impact")
    row = sim.timeline[-1]
    events = [item for item in sim.state.chronological_event_log if item.get("source_action_id") == "lynae_visual_impact" and item.get("packet_group_id")]
    assert len(events) == 1 and row.normal_damage == 0.0 and row.scheduled_damage == events[0]["damage"]
    payload = events[0]["damage_payload"], events[0]["resource_payload"]
    assert payload[0]["damage_multiplier"] == 12.1672
    assert (payload[1]["off_tune_value"], payload[1]["resonance_energy_gain"], payload[1]["concerto_energy_gain"]) == (609.6, 14.05, 14.58)
    assert sum(item.get("damage", 0.0) for item in events) == row.scheduled_damage
    print("lynae_visual_impact_payload_parity_no_duplicate_v124_smoke_test ok")


if __name__ == "__main__": main()
