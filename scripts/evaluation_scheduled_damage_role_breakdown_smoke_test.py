from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.damage_attribution import effective_damage_role_breakdown  # noqa: E402


def main() -> None:
    rows = [
        {
            "total_action_damage": 100.0,
            "normal_damage": 40.0,
            "tune_break_damage": 10.0,
            "tune_response_damage": 20.0,
            "generated_mechanic_damage": 5.0,
            "scheduled_damage": 15.0,
        }
    ]
    breakdown = effective_damage_role_breakdown(rows, 100.0)
    assert breakdown["scheduled_damage"] == 15.0
    assert breakdown["unclassified_damage"] == 10.0
    assert breakdown["total_damage_check"] == 100.0
    assert breakdown["total_damage_delta"] == 0.0
    assert (
        breakdown["normal_damage"]
        + breakdown["tune_break_damage"]
        + breakdown["tune_response_damage"]
        + breakdown["generated_mechanic_damage"]
        + breakdown["scheduled_damage"]
        + breakdown["unclassified_damage"]
    ) == breakdown["reported_total_damage"]
    print("evaluation_scheduled_damage_role_breakdown_smoke_test ok")


if __name__ == "__main__":
    main()
