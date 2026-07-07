from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ACTIONS_PATH = DATA_DIR / "actions.json"
OUTPUT_PATH = DATA_DIR / "extracted" / "mornye_relative_momentum_repeat_audit.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "mornye_relative_momentum_repeat_audit.md"


EXPECTED = {
    "mornye_wfo_basic_stage_1": {
        "relative_momentum_delta": 10.0,
        "source_rows": [4128],
        "source_status": "workbook_confirmed_repeat_aware",
        "repeat_calculation": "2.5 x 4",
    },
    "mornye_wfo_basic_stage_2": {
        "relative_momentum_delta": 12.0,
        "source_rows": [4129],
        "source_status": "workbook_confirmed_repeat_aware",
        "repeat_calculation": "3 x 4",
    },
    "mornye_wfo_basic_stage_3": {
        "relative_momentum_delta": 18.0,
        "source_rows": [4132, 4133],
        "source_status": "workbook_confirmed",
        "repeat_calculation": "9 + 9",
    },
    "mornye_skill_distributed_array": {
        "relative_momentum_delta": 60.0,
        "source_rows": [4144, 4145, 4146, 4147],
        "source_status": "workbook_confirmed",
        "repeat_calculation": "15 x 4",
    },
    "mornye_heavy_inversion": {
        "relative_momentum_delta": -100.0,
        "source_rows": [4135, 4136],
        "source_status": "not_source_confirmed_direct_interfered",
        "repeat_calculation": "consume 100",
    },
}


def assert_close(actual: float, expected: float, label: str) -> None:
    assert math.isclose(float(actual), float(expected), rel_tol=1e-9, abs_tol=1e-9), (
        f"{label}: expected {expected}, got {actual}"
    )


def action_by_id(actions: list[dict[str, Any]], action_id: str) -> dict[str, Any]:
    for action in actions:
        if action.get("id") == action_id:
            return action
    raise AssertionError(f"Missing action {action_id}")


def source_rows_for_effects(effects: dict[str, Any], action_id: str) -> list[int]:
    if action_id in {"mornye_wfo_basic_stage_1", "mornye_wfo_basic_stage_2"}:
        return list(effects.get("source_rows") or [])
    if action_id in {"mornye_wfo_basic_stage_3", "mornye_skill_distributed_array"}:
        return list(effects.get("relative_momentum_gain_source_rows") or [])
    return list(effects.get("source_rows") or [])


def relative_momentum_delta(effects: dict[str, Any]) -> float:
    if effects.get("consume_relative_momentum"):
        return -100.0
    return float(effects.get("relative_momentum_delta", 0.0))


def audit_actions(actions: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for action_id, expected in EXPECTED.items():
        action = action_by_id(actions, action_id)
        effects = dict(action.get("mechanic_effects") or {})
        actual_delta = relative_momentum_delta(effects)
        actual_rows = source_rows_for_effects(effects, action_id)
        actual_status = effects.get("source_status") or expected["source_status"]
        assert_close(actual_delta, expected["relative_momentum_delta"], f"{action_id} relative_momentum_delta")
        assert actual_rows == expected["source_rows"], (
            f"{action_id} source rows: expected {expected['source_rows']}, got {actual_rows}"
        )
        assert actual_status == expected["source_status"], (
            f"{action_id} source_status: expected {expected['source_status']}, got {actual_status}"
        )
        if action_id == "mornye_heavy_inversion":
            assert effects.get("consume_relative_momentum") is True
            assert effects.get("observation_marker_duration") == 30

        rows.append(
            {
                "action_id": action_id,
                "relative_momentum_delta": actual_delta,
                "source_rows": actual_rows,
                "source_status": actual_status,
                "repeat_calculation": expected["repeat_calculation"],
                "action_time": action.get("action_time"),
                "combat_time_cost": action.get("combat_time_cost"),
            }
        )
    return {
        "source": str(ACTIONS_PATH.relative_to(PROJECT_ROOT)),
        "summary": {
            "wfo_stage_1_changed_from": 2.5,
            "wfo_stage_1_changed_to": 10.0,
            "wfo_stage_2_changed_from": 3.0,
            "wfo_stage_2_changed_to": 12.0,
            "wfo_stage_3_unchanged": 18.0,
            "distributed_array_unchanged": 60.0,
            "heavy_inversion_consumes": 100.0,
        },
        "actions": rows,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Mornye Relative Momentum Repeat Audit",
        "",
        "| Action | Relative Momentum delta | Source rows | Source status | Calculation |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in payload["actions"]:
        lines.append(
            "| {action_id} | {relative_momentum_delta:g} | {source_rows} | {source_status} | {repeat_calculation} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Route Implication",
            "",
            "Distributed Array + WFO A1 + WFO A2 + WFO A3 now reaches 100 Relative Momentum: 60 + 10 + 12 + 18.",
            "Heavy Inversion still consumes 100 Relative Momentum and applies Observation Marker.",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    actions = json.loads(ACTIONS_PATH.read_text(encoding="utf-8"))
    payload = audit_actions(actions)
    write_outputs(payload)
    print("mornye_relative_momentum_repeat_audit ok")


if __name__ == "__main__":
    main()
