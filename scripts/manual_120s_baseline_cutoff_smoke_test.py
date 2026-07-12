from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manual_120s_baseline import TIMELINE_PATH, execute_route, write_outputs


def main() -> None:
    output = write_outputs()
    first = output["results"]["primary"]
    second = execute_route("primary")
    final = first["final_clipped_action"]
    assert final == second["final_clipped_action"]
    assert final["truncated_by_combat_limit"] is True
    assert final["start_time"] < 120.0
    assert final["end_time"] == 120.0
    assert final["effective_clipped_cost"] < final["full_combat_time_cost"]
    assert final["damage_after_cutoff_excluded"] > 0.0
    for effect in first["remaining_scheduled_effects_at_cutoff"]:
        next_time = effect.get("next_trigger_time")
        if next_time is not None:
            assert float(next_time) >= 120.0
    with TIMELINE_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    sequences = [int(row["timeline_sequence"]) for row in rows]
    assert sequences == sorted(sequences)
    scheduled_sequences = [
        int(row["scheduled_event_sequence"])
        for row in rows
        if row["scheduled_event_sequence"]
    ]
    assert scheduled_sequences == sorted(scheduled_sequences)
    print("manual_120s_baseline_cutoff_smoke_test ok")


if __name__ == "__main__":
    main()
