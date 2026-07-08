from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    actions = {action["id"]: action for action in json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))}
    tune_break = actions["lynae_tune_break"]
    report = (ROOT / "reports" / "lynae_timing_cooldown_audit.md").read_text(encoding="utf-8")

    assert tune_break["action_type"] == "tune_break"
    assert tune_break["damage_category"] == "tune_break"
    assert tune_break["damage_element"] is None
    assert tune_break["damage_multiplier"] == 0.0
    assert len(tune_break["hits"]) == 1
    hit = tune_break["hits"][0]
    assert hit["name"] == "lynae_tune_break_1"
    assert hit["time"] == 1.2
    assert hit["damage_category"] == "tune_break"
    assert hit["damage_multiplier"] == 0.0
    assert hit["tune_break_multiplier"] == 16.0
    assert "tune_break" in hit["tags"]
    assert tune_break["action_time"] == 1.6
    assert tune_break["combat_time_cost"] == 0.0
    assert {2702, 2703, 2704, 2488}.issubset(set(tune_break["source_rows"]))
    assert "workbook_confirmed_global_timestop" in tune_break["source_status"]
    assert "Tune Break" in report
    assert "global time stop row `2703`" in report
    assert "RateLv10 is not used as normal ATK/Spectro damage" in tune_break["notes"]

    print("lynae_tune_break_global_timestop_guard_smoke_test ok")


if __name__ == "__main__":
    main()
