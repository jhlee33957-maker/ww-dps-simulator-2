from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def execute_to_geopotential(sim: Simulation):
    for action_id in (
        "mornye_resonance_skill",
        "mornye_basic_attack",
        "mornye_basic_attack",
        "mornye_basic_attack",
        "mornye_heavy_attack",
    ):
        assert sim.execute_action(action_id), action_id
    return sim.timeline[-1]


def main() -> None:
    sim = Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character="mornye")
    heavy = execute_to_geopotential(sim)
    damage_events = [event for event in heavy.scheduled_damage_events if event.get("event_type") == "scheduled_damage"]
    heal_events = [event for event in heavy.scheduled_damage_events if event.get("event_type") == "scheduled_heal"]
    assert [event["payload_action_id"] for event in damage_events] == [
        "mornye_syntony_field_damage",
        "mornye_syntony_field_target_damage",
        "mornye_syntony_field_damage",
    ]
    assert [event["payload_action_id"] for event in heal_events] == ["mornye_syntony_field_heal"]
    damage_1 = sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_1:mornye")
    assert damage_1 is not None
    assert damage_1.trigger_count == 2
    assert sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_2:mornye") is None

    assert sim.execute_action("mornye_resonance_liberation")
    liberation = sim.timeline[-1]
    assert liberation.resolved_action_id == "mornye_liberation_critical_protocol"
    assert_close(liberation.combat_time_cost, 0.0, "Critical Protocol combat time")
    assert liberation.scheduled_damage_events == []
    assert liberation.high_syntony_field_active is True
    assert sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_1:mornye") is None
    assert sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_2:mornye") is None

    before_log_count = len(sim.state.scheduled_effect_event_log)
    assert sim.execute_action("mornye_basic_attack")
    later = sim.timeline[-1]
    assert [event["event_type"] for event in later.scheduled_damage_events] == ["scheduled_heal"]
    assert later.scheduled_healing_events[0]["payload_action_id"] == "mornye_high_syntony_field_heal"
    assert len(sim.state.scheduled_effect_event_log) == before_log_count + 1

    print("mornye_high_syntony_field_scheduler_cancel_smoke_test ok")


if __name__ == "__main__":
    main()
