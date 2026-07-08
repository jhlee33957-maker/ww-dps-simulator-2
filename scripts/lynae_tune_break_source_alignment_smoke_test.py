from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    action_map = json.loads((ROOT / "data" / "extracted" / "lynae_excel_action_map.json").read_text(encoding="utf-8"))
    records = {record["action_id"]: record for record in action_map}
    record = records["lynae_tune_break"]

    assert record["implementation_status"] == "excel_tune_break_single_target_v1"
    assert record["source_status"] == "workbook_confirmed_global_timestop_tune_break_damage"
    assert record["multiplier"] == 0.0
    assert record["normal_damage_multiplier"] == 0.0
    assert record["tune_break_multiplier"] == 16.0
    assert record["tune_break_multiplier_source_row"] == 2488
    assert record["tune_break_multiplier_source_column"] == "Damage.RateLv_1"
    assert record["tune_break_hit_frame"] == 72
    assert record["tune_break_hit_time"] == 1.2
    assert record["action_window_frames"] == 96
    assert record["global_time_stop_row"] == 2703
    assert record["damage_rows"] == [2488]
    assert record["action_rows"] == [2702, 2703, 2704]
    assert record["damage_row_rate_lv_1_multipliers"]["2488"] == 16.0

    alignment_report = (ROOT / "reports" / "lynae_excel_source_alignment.md").read_text(encoding="utf-8")
    timing_report = (ROOT / "reports" / "lynae_timing_cooldown_audit.md").read_text(encoding="utf-8")
    combined_reports = alignment_report + "\n" + timing_report
    assert "dmg!2488 RateLv1 `160000`" in combined_reports
    assert "Tune Break multiplier `16.0`" in combined_reports
    assert "RateLv10 is not used as normal ATK/Spectro damage" in combined_reports
    assert "global time stop" in combined_reports
    assert "72F" in combined_reports
    assert "96F" in combined_reports
    assert "metadata_only_zero_workbook_damage" not in alignment_report.split("`lynae_tune_break`", 1)[1].splitlines()[0]

    print("lynae_tune_break_source_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
