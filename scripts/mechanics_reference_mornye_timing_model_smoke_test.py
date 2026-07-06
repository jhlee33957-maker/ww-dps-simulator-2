from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.mechanics_reference import load_mechanics_data


def _text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).lower()


def _row_by_name(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for row in rows:
        if row.get("name") == name:
            return row
    raise AssertionError(f"missing timing_model row: {name}")


def _assert_close(actual: float, expected: float, tolerance: float = 1e-4) -> None:
    assert math.isclose(float(actual), expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"expected {expected}, got {actual}"
    )


def main() -> None:
    mornye = load_mechanics_data("mornye")
    aemeath = load_mechanics_data("aemeath")

    assert "timing_model" in mornye, "Mornye mechanics reference should include timing_model"
    assert mornye["timing_model"], "Mornye timing_model should not be empty"
    assert "timing_model" in aemeath, "Aemeath timing_model should still exist"

    timing_model = mornye["timing_model"]
    critical_protocol = _row_by_name(timing_model, "Critical Protocol / Resonance Liberation")
    _assert_close(critical_protocol["action_time"], 4.9333)
    _assert_close(critical_protocol["combat_time_cost"], 0.0)
    assert "global time stop" in _text(critical_protocol)

    heavy_inversion = _row_by_name(timing_model, "Heavy Inversion")
    _assert_close(heavy_inversion["action_time"], 1.3)
    _assert_close(heavy_inversion["combat_time_cost"], 1.3)

    intro = _row_by_name(timing_model, "Convergence / Intro")
    _assert_close(intro["action_time"], 1.7)

    timing_text = _text(timing_model)
    assert "selector/wrapper actions are routing placeholders" in timing_text
    assert "0.1s placeholder timing" in timing_text
    assert "exact hit-level timing" in timing_text
    assert "not fully modeled" in timing_text

    print("Mornye timing_model mechanics reference smoke test passed.")


if __name__ == "__main__":
    main()
