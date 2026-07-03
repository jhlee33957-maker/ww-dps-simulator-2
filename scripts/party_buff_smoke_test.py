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


def first_aemeath_basic_damage() -> float:
    sim = Simulation.from_json(DATA_DIR, party="aemeath")
    assert sim.execute_action("aemeath_basic_attack")
    return sim.timeline[-1].total_action_damage


def active_buff_remaining(sim: Simulation, buff_id: str) -> float:
    for buff in sim.state.active_buffs:
        if buff.buff_id == buff_id:
            return buff.remaining_duration
    return 0.0


def main() -> None:
    baseline_damage = first_aemeath_basic_damage()

    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    assert sim.execute_action("swap_to_dummy_support")
    assert sim.execute_action("dummy_support_buff")
    assert active_buff_remaining(sim, "dummy_support_damage_amp") == 20.0
    assert sim.timeline[-1].applied_buffs == ["dummy_support_damage_amp"]
    assert sim.party_state.team_buffs

    assert sim.execute_action("swap_to_aemeath")
    after_swap_remaining = active_buff_remaining(sim, "dummy_support_damage_amp")
    outro_remaining = active_buff_remaining(sim, "dummy_support_outro_damage_amp")
    assert after_swap_remaining > 0.0
    assert after_swap_remaining < 20.0
    assert outro_remaining == 20.0
    assert "dummy_support_outro_damage_amp" in sim.timeline[-1].applied_buffs

    assert sim.execute_action("aemeath_basic_attack")
    buffed_damage = sim.timeline[-1].total_action_damage
    assert buffed_damage > baseline_damage * 1.39
    assert "dummy_support_damage_amp" in sim.timeline[-1].active_buffs
    assert "dummy_support_outro_damage_amp" in sim.timeline[-1].active_buffs
    assert active_buff_remaining(sim, "dummy_support_damage_amp") < after_swap_remaining

    while (
        active_buff_remaining(sim, "dummy_support_damage_amp") > 0.0
        or active_buff_remaining(sim, "dummy_support_outro_damage_amp") > 0.0
    ):
        assert sim.execute_action("short_wait")
    assert_close(active_buff_remaining(sim, "dummy_support_damage_amp"), 0.0, "expired buff")
    assert_close(active_buff_remaining(sim, "dummy_support_outro_damage_amp"), 0.0, "expired outro buff")
    assert sim.party_state.team_buffs == []

    print("Party buff smoke test passed.")


if __name__ == "__main__":
    main()
