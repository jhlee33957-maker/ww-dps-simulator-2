from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    sim = Simulation.from_json("data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    before = (sim.state.current_time, sim.state.combat_time)
    assert sim.execute_action("aemeath_echo_sigillum")
    row = sim.timeline[-1]

    assert row.action_id == "aemeath_echo_sigillum"
    assert_close(row.action_time, 0.0, "action time")
    assert_close(row.combat_time_cost, 0.0, "combat time cost")
    assert_close(row.combat_time_start, row.combat_time_end, "combat time unchanged in row")
    assert (sim.state.current_time, sim.state.combat_time) == before
    assert row.aemeath_sigillum_activation_scheduled is True
    assert_close(row.aemeath_sigillum_activation_combat_time, 0.0, "activation time")
    assert row.aemeath_sigillum_source_end_frame == 80
    assert [event["hit_index"] for event in row.aemeath_sigillum_hit_schedule_events] == [1, 2]
    assert len(sim.state.scheduled_effects) == 2
    assert_close(sim.state.cooldowns["aemeath_echo_sigillum"], 20.0, "cooldown")
    assert not sim.execute_action("aemeath_echo_sigillum")
    assert len(sim.state.scheduled_effects) == 2
    print("aemeath_sigillum_zero_time_activation_smoke_test ok")


if __name__ == "__main__":
    main()
