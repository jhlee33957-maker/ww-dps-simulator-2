from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def make_sim() -> Simulation:
    return Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])


def aemeath_state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["aemeath"]


def set_finale_ready(sim: Simulation) -> None:
    data = aemeath_state(sim)
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["synchronization_rate"] = 200.0
    data["resonance_rate"] = 4.0
    sim.character_mechanics["aemeath"].advance_time(sim.state, 0.0)


def test_final_aemeath_action_is_clipped() -> None:
    sim = make_sim()
    sim.state.combat_time = 119.9
    assert sim.execute_action("aemeath_basic_attack")
    summary = sim.summary()
    row = summary.timeline[-1]

    assert summary.final_time <= 120.0 + 1e-9
    assert_close(summary.final_time, 120.0, "Aemeath summary final_time")
    assert row.combat_time_end <= 120.0 + 1e-9
    assert row.truncated_by_combat_limit is True
    assert_close(row.effective_combat_time_cost, 0.1, "Aemeath clipped combat cost")


def test_zero_cost_overdrive_before_limit_remains_valid() -> None:
    sim = make_sim()
    sim.state.combat_time = 119.9
    sim.state.resonance_energy["aemeath"] = 125.0
    sim.state.cooldowns["probe"] = 10.0
    assert sim.execute_action("aemeath_resonance_liberation")
    row = sim.timeline[-1]

    assert row.resolved_action_id == "aemeath_liberation_overdrive"
    assert_close(row.combat_time_start, 119.9, "Overdrive combat_time_start")
    assert_close(row.combat_time_end, 119.9, "Overdrive combat_time_end")
    assert_close(row.effective_combat_time_cost, 0.0, "Overdrive effective combat cost")
    assert row.truncated_by_combat_limit is False
    assert_close(sim.state.cooldowns["probe"], 10.0, "Overdrive cooldown tick")


def test_no_finale_after_limit() -> None:
    sim = make_sim()
    set_finale_ready(sim)
    sim.state.combat_time = 120.0
    before_timeline_len = len(sim.timeline)
    assert sim.execute_action("aemeath_resonance_liberation") is False
    assert len(sim.timeline) == before_timeline_len
    finale_count = sum(
        1
        for row in sim.timeline
        if (row.resolved_action_id or row.action_id) == "aemeath_heavenfall_finale"
    )
    assert finale_count == 0


def main() -> None:
    test_final_aemeath_action_is_clipped()
    test_zero_cost_overdrive_before_limit_remains_valid()
    test_no_finale_after_limit()
    print("Aemeath evaluation cutoff smoke test passed.")


if __name__ == "__main__":
    main()
