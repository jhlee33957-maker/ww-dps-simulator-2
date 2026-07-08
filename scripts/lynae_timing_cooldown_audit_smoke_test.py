from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    json_path = ROOT / "data" / "extracted" / "lynae_timing_cooldown_audit.json"
    report_path = ROOT / "reports" / "lynae_timing_cooldown_audit.md"
    assert json_path.exists()
    assert report_path.exists()

    audit = json.loads(json_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    records = {record["action_id"]: record for record in audit["records"]}
    overblast = records["lynae_resonance_liberation_prismatic_overblast"]
    tune_break = records["lynae_tune_break"]
    skill_selector = records["lynae_resonance_skill"]
    palette = records["lynae_resonance_skill_palette"]
    additive = records["lynae_resonance_skill_additive_color"]
    outro = records["lynae_outro_lets_hit_the_road"]

    assert overblast["action_time"] == 4.0
    assert overblast["combat_time_cost"] == 0.0
    assert overblast["global_time_stop_rows"] == [2693]
    assert overblast["global_time_stop_frames"] == 240
    assert overblast["cooldown"] == 25
    assert overblast["resource_cost"] == 125
    assert tune_break["action_time"] == 1.6
    assert tune_break["combat_time_cost"] == 0.0
    assert tune_break["global_time_stop_rows"] == [2703]
    assert tune_break["action_type"] == "tune_break"
    assert tune_break["hit_count"] == 1
    assert tune_break["tune_break_multiplier"] == 16.0
    assert tune_break["source_status"] == "workbook_confirmed_global_timestop_tune_break_damage"
    assert skill_selector["cooldown"] == 6.0
    assert skill_selector["cooldown_group"] == "lynae_resonance_skill"
    assert skill_selector["immediate_repeat_allowed"] is False
    assert "cooldown" in skill_selector["immediate_repeat_reason"]
    assert palette["cooldown"] == 6.0
    assert additive["cooldown"] == 6.0
    assert palette["cooldown_group"] == "lynae_resonance_skill"
    assert additive["cooldown_group"] == "lynae_resonance_skill"
    assert outro["policy_selectable"] is False
    assert outro["action_type"] == "swap"
    assert "transition" in outro["immediate_repeat_reason"]
    assert "lynae_resonance_skill`" in report
    assert "repeatable only if policy path and mechanic gates permit it" not in report.split("| `lynae_resonance_skill`", 1)[1].splitlines()[0]
    assert "299F is the timed-combat duration" not in report
    assert "action_time `4.9833`" not in report
    assert "dmg!2488 RateLv1 `160000`" in report
    assert "RateLv10 is not used as normal ATK/Spectro damage" in report

    print("lynae_timing_cooldown_audit_smoke_test ok")


if __name__ == "__main__":
    main()
