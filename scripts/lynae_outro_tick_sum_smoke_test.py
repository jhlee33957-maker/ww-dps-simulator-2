from __future__ import annotations

import json
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    runpy.run_path(str(ROOT / "scripts/lynae_source_audit.py"), run_name="__main__")
    action_map = {
        record["action_id"]: record
        for record in json.loads((ROOT / "data/extracted/lynae_excel_action_map.json").read_text(encoding="utf-8"))
    }
    outro_map = action_map["lynae_outro_lets_hit_the_road"]
    assert outro_map["calculation_type"] == "excel_tick_sum_and_tooltip_confirmed"
    assert abs(outro_map["derived_tick_sum"] - 1.001) < 1e-9
    assert outro_map["damage_row_rate_lv_1_multipliers"] == {"2486": 0.0455, "2487": 0.0455}

    actions = {item["id"]: item for item in json.loads((ROOT / "data/actions.json").read_text(encoding="utf-8"))}
    outro = actions["lynae_outro_lets_hit_the_road"]
    assert abs(outro["damage_multiplier"] - 1.0) < 1e-9
    assert outro["source_status"] == "excel_tick_sum_and_tooltip_confirmed"
    assert abs(outro["metadata"]["derived_tick_sum"] - 1.001) < 1e-9
    print("lynae_outro_tick_sum_smoke_test ok")


if __name__ == "__main__":
    main()
