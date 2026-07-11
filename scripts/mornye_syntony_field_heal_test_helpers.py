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
NORMAL_HEAL = "mornye_syntony_field_heal:mornye"
HIGH_HEAL = "mornye_high_syntony_field_heal:mornye"
NORMAL_FRAMES = [1, 181, 361, 541, 721, 901, 1081, 1261, 1441]
EXPECTED_NORMAL_DEF = 2997.0536
EXPECTED_NORMAL_HEAL = 4637.215652
EXPECTED_HIGH_DEF = 3268.2536
EXPECTED_HIGH_HEAL = 6850.8995128


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def make_sim(initial_active: str = "mornye") -> Simulation:
    return Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character=initial_active)


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


def scheduled_heals(sim: Simulation) -> list[dict]:
    return [event for event in sim.state.scheduled_effect_event_log if event.get("event_type") == "scheduled_heal"]


def frame_offsets(events: list[dict], activation_time: float) -> list[int]:
    return [round((event["combat_time"] - activation_time) * 60) for event in events]


def advance_until_no_effect(sim: Simulation, instance_id: str, limit: int = 400) -> None:
    for _ in range(limit):
        if sim.scheduled_effect_by_instance_id(instance_id) is None:
            return
        assert sim.execute_action("short_wait")
    raise AssertionError(f"{instance_id} did not expire")
