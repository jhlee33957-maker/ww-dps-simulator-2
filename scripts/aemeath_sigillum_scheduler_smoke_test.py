from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    sim = Simulation.from_json("data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    sim.state.resonance_energy["aemeath"] = 0.0
    assert sim.execute_action("aemeath_echo_sigillum")
    assert sim.execute_action("short_wait")
    first = sim.timeline[-1].scheduled_damage_events
    assert [event["hit_index"] for event in first] == [1]
    assert_close(first[0]["combat_time"], 25.0 / 60.0, "hit 1 due time")
    assert_close(first[0]["base_resonance_energy_gain"], 0.23, "hit 1 base RE")
    assert_close(first[0]["final_resonance_energy_gain"], 0.276, "hit 1 final RE")

    assert sim.execute_action("short_wait")
    second = sim.timeline[-1].scheduled_damage_events
    assert [event["hit_index"] for event in second] == [2]
    assert_close(second[0]["combat_time"], 55.0 / 60.0, "hit 2 due time")
    assert_close(second[0]["base_resonance_energy_gain"], 2.13, "hit 2 base RE")
    assert_close(second[0]["final_resonance_energy_gain"], 2.556, "hit 2 final RE")
    assert_close(sim.state.resonance_energy["aemeath"], 2.832, "Aemeath total RE")
    assert len(sim.state.scheduled_effects) == 0
    assert len([event for event in sim.state.scheduled_effect_event_log if event["source_action_id"] == "aemeath_echo_sigillum"]) == 2
    print("aemeath_sigillum_scheduler_smoke_test ok")


if __name__ == "__main__":
    main()
