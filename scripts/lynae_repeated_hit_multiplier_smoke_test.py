from __future__ import annotations

import json
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def assert_close(actual: float, expected: float, label: str) -> None:
    assert abs(actual - expected) < 1e-9, f"{label}: expected {expected}, got {actual}"


def action_map_by_id() -> dict[str, dict]:
    runpy.run_path(str(ROOT / "scripts/lynae_source_audit.py"), run_name="__main__")
    records = json.loads((ROOT / "data/extracted/lynae_excel_action_map.json").read_text(encoding="utf-8"))
    return {record["action_id"]: record for record in records}


def main() -> None:
    by_id = action_map_by_id()
    expected = {
        "lynae_kaleidoscopic_basic_stage_5": 2.5181,
        "lynae_polychrome_leap_stage_2": 1.0140,
        "lynae_polychrome_leap_stage_3": 0.6550,
        "lynae_intro_time_to_show_some_colors": 2.2480,
        "lynae_resonance_liberation_prismatic_overblast": 8.7480,
        "lynae_to_a_vivid_tomorrow": 2.0106,
    }
    for action_id, multiplier in expected.items():
        record = by_id[action_id]
        assert "repeated" in record["calculation_type"], record
        assert record.get("repeated_tick_rows"), record
        assert_close(record["multiplier"], multiplier, action_id)
    print("lynae_repeated_hit_multiplier_smoke_test ok")


if __name__ == "__main__":
    main()
