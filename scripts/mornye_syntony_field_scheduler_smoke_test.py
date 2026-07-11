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


def make_sim() -> Simulation:
    return Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character="mornye")


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


def event_frames(row, combat_start: float) -> list[int]:
    return [round((event["combat_time"] - combat_start) * 60) for event in row.scheduled_damage_events]


def source_multiplier(events: list[dict]) -> float:
    return sum(float(event["hit_details"][0]["damage_multiplier"]) for event in events)


def test_heavy_host_activation_timing() -> None:
    sim = make_sim()
    row = execute_to_geopotential(sim)
    assert row.resolved_action_id == "mornye_heavy_geopotential_shift"
    activation_time = row.combat_time_start + 48.0 / 60.0
    assert_close(row.combat_time_end - row.combat_time_start, 80.0 / 60.0, "heavy combat frames")

    assert event_frames(row, row.combat_time_start) == [49, 71, 76]
    assert [event["payload_action_id"] for event in row.scheduled_damage_events] == [
        "mornye_syntony_field_damage",
        "mornye_syntony_field_target_damage",
        "mornye_syntony_field_damage",
    ]
    assert_close(source_multiplier(row.scheduled_damage_events), 1.7856, "heavy-host source multiplier")

    damage_1 = sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_1:mornye")
    damage_2 = sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_2:mornye")
    assert damage_1 is not None
    assert damage_2 is None
    assert_close(damage_1.activation_combat_time, activation_time, "Damage 1 activation")
    assert damage_1.trigger_count == 2
    assert damage_1.max_trigger_count == 5
    assert damage_1.scheduled_resource_policy == "none"


def test_full_uncancelled_burst() -> None:
    sim = make_sim()
    row = execute_to_geopotential(sim)
    activation_time = row.combat_time_start + 48.0 / 60.0

    while sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_1:mornye") is not None:
        assert sim.execute_action("mornye_basic_attack")

    deployment_events = [
        event
        for event in sim.state.scheduled_effect_event_log
        if event["scheduled_effect_instance_id"].startswith("mornye_syntony_field_damage_")
    ]
    frames = [round((event["combat_time"] - activation_time) * 60) for event in deployment_events]
    assert frames == [1, 23, 28, 55, 82, 109]
    assert [event["payload_action_id"] for event in deployment_events].count("mornye_syntony_field_damage") == 5
    assert [event["payload_action_id"] for event in deployment_events].count("mornye_syntony_field_target_damage") == 1
    assert_close(source_multiplier(deployment_events), 2.9787, "full source multiplier")
    assert_close(sum(float(event.get("off_tune_value", 0.0)) for event in deployment_events), 66.4, "raw Off-Tune")
    assert_close(
        sum(float(event.get("off_tune_gain", 0.0)) for event in deployment_events),
        99.6,
        "applied Off-Tune",
    )


def main() -> None:
    test_heavy_host_activation_timing()
    test_full_uncancelled_burst()
    print("mornye_syntony_field_scheduler_smoke_test ok")


if __name__ == "__main__":
    main()
