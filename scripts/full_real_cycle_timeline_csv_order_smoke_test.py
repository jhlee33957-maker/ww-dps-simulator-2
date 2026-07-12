from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIMELINE_CSV = ROOT / "results" / "full_real_cycle_integration_v103_timeline.csv"


def main() -> None:
    with TIMELINE_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    required_columns = {"timeline_sequence", "timeline_sort_sequence", "scheduled_event_sequence"}
    assert required_columns.issubset(rows[0])

    same_time_rows = [
        row
        for row in rows
        if math.isclose(float(row["time"]), 7.8, rel_tol=0.0, abs_tol=1e-9)
        and row["payload_action_id"] in {"mornye_syntony_field_heal", "mornye_syntony_field_damage"}
    ]
    assert [row["payload_action_id"] for row in same_time_rows[:2]] == [
        "mornye_syntony_field_heal",
        "mornye_syntony_field_damage",
    ]
    assert [row["event_type"] for row in same_time_rows[:2]] == ["scheduled_heal", "scheduled_damage"]
    assert int(same_time_rows[0]["timeline_sequence"]) < int(same_time_rows[1]["timeline_sequence"])
    assert int(same_time_rows[0]["scheduled_event_sequence"]) < int(same_time_rows[1]["scheduled_event_sequence"])

    policy_at_same_time: dict[float, list[int]] = {}
    for row in rows:
        if row["kind"] != "policy_action":
            continue
        policy_at_same_time.setdefault(float(row["time"]), []).append(int(row["policy_step"]))
    for steps in policy_at_same_time.values():
        assert steps == sorted(steps)

    print("full_real_cycle_timeline_csv_order_smoke_test ok")


if __name__ == "__main__":
    main()
