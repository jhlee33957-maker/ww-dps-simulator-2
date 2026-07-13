from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def make_late_sigillum(combat_time: float) -> Simulation:
    sim = Simulation.from_json("data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    sim.state.current_time = combat_time
    sim.state.combat_time = combat_time
    sim.state.resonance_energy["aemeath"] = 0.0
    assert sim.execute_action("aemeath_echo_sigillum")
    return sim


def main() -> None:
    too_late = make_late_sigillum(119.99)
    assert too_late.execute_action("short_wait")
    assert too_late.timeline[-1].combat_time_end == 120.0
    assert too_late.timeline[-1].scheduled_damage_events == []
    assert too_late.state.resonance_energy["aemeath"] == 0.0
    assert len(too_late.state.scheduled_effects) == 2

    first_only = make_late_sigillum(119.50)
    assert first_only.execute_action("short_wait")
    events = first_only.timeline[-1].scheduled_damage_events
    assert [event["hit_index"] for event in events] == [1]
    assert first_only.state.resonance_energy["aemeath"] == 0.276
    assert len(first_only.state.scheduled_effects) == 1
    print("aemeath_sigillum_combat_cutoff_smoke_test ok")


if __name__ == "__main__":
    main()
