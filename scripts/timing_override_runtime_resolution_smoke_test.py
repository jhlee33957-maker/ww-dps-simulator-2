from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.action_executor import resolve_action_runtime_timing, resolve_action_timing
from simulator.models import ActionData


DATA_DIR = PROJECT_ROOT / "data"


def actions_by_id() -> dict[str, ActionData]:
    records = json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8"))
    return {record["id"]: ActionData.model_validate(record) for record in records}


def assert_timing(action: ActionData, context: dict, expected_action_time: float, expected_combat_time: float) -> None:
    duration, action_time, combat_time_cost = resolve_action_runtime_timing(action, context)
    legacy_action_time, legacy_combat_time_cost = resolve_action_timing(action, context)
    assert duration > 0.0
    assert math.isclose(action_time, expected_action_time, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(combat_time_cost, expected_combat_time, rel_tol=1e-9, abs_tol=1e-9)
    assert legacy_action_time == action_time
    assert legacy_combat_time_cost == combat_time_cost


def main() -> None:
    actions = actions_by_id()

    assert_timing(actions["aemeath_tune_break"], {"form": "aemeath"}, 90 / 60, 0.0)
    assert_timing(actions["aemeath_tune_break"], {"form": "mech"}, 94 / 60, 0.0)

    assert_timing(actions["mornye_liberation_critical_protocol"], {"mode": "normal"}, 282 / 60, 0.0)
    assert_timing(
        actions["mornye_liberation_critical_protocol"],
        {"mode": "wide_field_observation"},
        296 / 60,
        0.0,
    )

    assert_timing(actions["lynae_kaleidoscopic_basic_stage_1"], {"lumiflow": 119.0}, 35 / 60, 35 / 60)
    assert_timing(actions["lynae_kaleidoscopic_basic_stage_1"], {"lumiflow": 120.0}, 40 / 60, 40 / 60)
    assert_timing(
        actions["lynae_kaleidoscopic_basic_stage_1"],
        {"lumiflow": 120.0, "has_valid_target": False},
        45 / 60,
        45 / 60,
    )


if __name__ == "__main__":
    main()
