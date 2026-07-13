from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manual_120s_baseline import REPORT_PATH, ROUTE_PATH, SUMMARY_PATH, TIMELINE_PATH, write_outputs


def _read_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf")
    assert b"\xef\xbf\xbd" not in data
    return data


def main() -> None:
    write_outputs()
    before = {path: _read_bytes(path) for path in (ROUTE_PATH, SUMMARY_PATH, TIMELINE_PATH, REPORT_PATH)}
    write_outputs()
    after = {path: _read_bytes(path) for path in before}
    assert before == after
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    routes = json.loads(ROUTE_PATH.read_text(encoding="utf-8"))
    assert summary["selected_sequence_sha256"] == routes["routes"]["primary"]["selected_sequence_sha256"]
    assert summary["resolved_sequence_sha256"] == routes["routes"]["primary"]["resolved_sequence_sha256"]
    for key in (
        "total_damage",
        "dps",
        "damage_by_character",
        "final_clipped_action",
        "resonance_energy",
        "concerto_energy",
        "active_echo_summary",
        "damage_by_damage_bonus_category",
        "uptime_summary",
    ):
        assert key in summary
    for resource_key in ("resonance_energy", "concerto_energy"):
        for bucket in ("initial", "gained", "spent", "wasted", "final", "direct", "scheduled"):
            assert bucket in summary[resource_key]
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    for phrase in (
        "## Resources",
        "## Damage Categories",
        "## Active Echo Damage",
        "## Uptime",
        "## Fields And Cutoff",
        "Remaining scheduled effects at cutoff",
    ):
        assert phrase in report_text
    with TIMELINE_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    for column in ("timeline_sequence", "policy_step", "scheduled_event_sequence", "source_character_id", "damage_attribution"):
        assert column in rows[0]
    assert [int(row["timeline_sequence"]) for row in rows] == list(range(1, len(rows) + 1))
    print("manual_120s_baseline_reporting_smoke_test ok")


if __name__ == "__main__":
    main()
