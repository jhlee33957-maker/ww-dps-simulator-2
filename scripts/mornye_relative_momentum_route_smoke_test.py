from __future__ import annotations

import math
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-4) -> None:
    assert math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def mornye_state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["mornye"]


def setup_wfo_sim() -> Simulation:
    sim = Simulation.from_json(DATA_DIR, party=["mornye"])
    state = mornye_state(sim)
    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 30.0
    state["relative_momentum"] = 0.0
    state["wfo_combo_stage"] = 1
    return sim


def test_distributed_array_wfo_combo_reaches_inversion() -> None:
    sim = setup_wfo_sim()

    assert sim.execute_action("mornye_resonance_skill")
    distributed = sim.timeline[-1]
    assert distributed.resolved_action_id == "mornye_skill_distributed_array"
    assert distributed.relative_momentum_gain == 60.0
    assert distributed.relative_momentum_gain_source_rows == [4144, 4145, 4146, 4147]
    assert distributed.source_status == "workbook_confirmed"

    assert sim.execute_action("mornye_basic_attack")
    stage_1 = sim.timeline[-1]
    assert stage_1.resolved_action_id == "mornye_wfo_basic_stage_1"
    assert stage_1.relative_momentum_gain == 10.0
    assert stage_1.relative_momentum_gain_source_rows == [4128]
    assert stage_1.source_status == "workbook_confirmed_repeat_aware"

    assert sim.execute_action("mornye_basic_attack")
    stage_2 = sim.timeline[-1]
    assert stage_2.resolved_action_id == "mornye_wfo_basic_stage_2"
    assert stage_2.relative_momentum_gain == 12.0
    assert stage_2.relative_momentum_gain_source_rows == [4129]
    assert stage_2.source_status == "workbook_confirmed_repeat_aware"

    assert sim.execute_action("mornye_basic_attack")
    stage_3 = sim.timeline[-1]
    assert stage_3.resolved_action_id == "mornye_wfo_basic_stage_3"
    assert stage_3.relative_momentum_gain == 18.0
    assert stage_3.relative_momentum_gain_source_rows == [4132, 4133]
    assert stage_3.source_status == "workbook_confirmed"

    state = mornye_state(sim)
    assert_close(state["relative_momentum"], 100.0, "Relative Momentum after DA + WFO A1/A2/A3")
    assert_close(sim.state.combat_time, 2.7167, "time to 100 Relative Momentum")
    assert sim.is_action_available(sim.actions["mornye_heavy_attack"]) is True

    assert sim.execute_action("mornye_heavy_attack")
    heavy = sim.timeline[-1]
    state = mornye_state(sim)
    assert heavy.resolved_action_id == "mornye_heavy_inversion"
    assert heavy.relative_momentum_gain == -100.0
    assert heavy.relative_momentum_gain_source_rows == [4135]
    assert state["relative_momentum"] == 0.0
    assert state["observation_marker_active"] is True
    assert 29.0 < state["observation_marker_remaining"] < 30.0
    assert_close(sim.state.combat_time, 4.15, "time through Heavy Inversion")


def main() -> None:
    test_distributed_array_wfo_combo_reaches_inversion()
    print("mornye_relative_momentum_route_smoke_test ok")


if __name__ == "__main__":
    main()
