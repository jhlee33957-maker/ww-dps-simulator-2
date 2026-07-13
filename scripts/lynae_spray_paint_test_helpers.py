from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
PARTY_ID = "aemeath_lynae_enabled_test_party"
INSTANCE_ID = "lynae_spray_paint_flux:lynae"
PAYLOAD_ID = "lynae_spray_paint_flux_application"
ROLE_FEMALE_SHEET = "\u89d2\u8272-\u5973"
TUNE_STRAIN_REF = f"{ROLE_FEMALE_SHEET}!2683"
TUNE_RUPTURE_REF = f"{ROLE_FEMALE_SHEET}!2684"
C1_OUT_OF_SCOPE_REFS = [f"{ROLE_FEMALE_SHEET}!{row}" for row in range(2685, 2689)]


def assert_canonical_source_refs() -> None:
    assert [ord(char) for char in ROLE_FEMALE_SHEET] == [0x89D2, 0x8272, 0x002D, 0x5973]
    assert TUNE_STRAIN_REF == "角色-女!2683"
    assert TUNE_RUPTURE_REF == "角色-女!2684"
    assert C1_OUT_OF_SCOPE_REFS == [
        "角色-女!2685",
        "角色-女!2686",
        "角色-女!2687",
        "角色-女!2688",
    ]


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def make_sim(mode: str = "tune_rupture") -> Simulation:
    sim = Simulation.from_json(DATA_DIR, party=PARTY_ID)
    sim.state.character_mechanics_state["lynae"]["lynae_resonance_mode"] = mode
    return sim


def prime_visual_impact(sim: Simulation, mode: str = "tune_rupture") -> None:
    state = sim.state.character_mechanics_state["lynae"]
    state["lynae_resonance_mode"] = mode
    state["overflow"] = 120.0
    assert sim.execute_action("lynae_spark_collision")
    for index in range(1, 4):
        assert sim.execute_action(f"lynae_polychrome_leap_stage_{index}")


def reset_visual_impact_availability(sim: Simulation, mode: str = "tune_rupture") -> None:
    state = sim.state.character_mechanics_state["lynae"]
    state["lynae_resonance_mode"] = mode
    state["true_color"] = 3.0
    state["lumiflow"] = 120.0
    state["kaleidoscopic_parade_remaining"] = 10.0
    state["visual_impact_cooldown_remaining"] = 0.0
    sim.state.cooldowns.pop("lynae_visual_impact", None)


def execute_visual_impact(mode: str = "tune_rupture") -> tuple[Simulation, object, float]:
    sim = make_sim(mode)
    prime_visual_impact(sim, mode)
    assert sim.execute_action("lynae_visual_impact")
    row = sim.timeline[-1]
    return sim, row, float(row.combat_time_end)


def collect_spray_events(sim: Simulation, activation_time: float, max_frames: int = 360) -> list[dict]:
    events: list[dict] = []
    while round((float(sim.state.combat_time) - activation_time) * 60) < max_frames:
        assert sim.execute_action("short_wait")
        events.extend(
            event
            for event in sim.timeline[-1].scheduled_status_application_events
            if event.get("payload_action_id") == PAYLOAD_ID
        )
    return events


def relative_frames(events: list[dict], activation_time: float) -> list[int]:
    return [round((float(event["combat_time"]) - activation_time) * 60) for event in events]
