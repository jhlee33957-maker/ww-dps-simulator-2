from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    runpy.run_path(str(ROOT / "scripts/lynae_source_audit.py"), run_name="__main__")
    action_map_path = ROOT / "data/extracted/lynae_excel_action_map.json"
    unresolved_path = ROOT / "data/extracted/lynae_excel_unresolved_rows.json"
    report_path = ROOT / "reports/lynae_excel_source_alignment.md"
    assert action_map_path.exists()
    assert unresolved_path.exists()
    assert report_path.exists()

    action_map = json.loads(action_map_path.read_text(encoding="utf-8"))
    by_id = {item["action_id"]: item for item in action_map}
    assert by_id["lynae_spark_collision_lv3"]["damage_rows"] == [2421, 2422]
    assert abs(by_id["lynae_spark_collision_lv3"]["multiplier"] - 5.5556) < 1e-9
    assert by_id["lynae_visual_impact"]["damage_rows"] == [2464, 2465]
    assert abs(by_id["lynae_tune_response_spectral_analysis"]["multiplier"] - 18.8075) < 1e-9

    unresolved = json.loads(unresolved_path.read_text(encoding="utf-8"))
    assert any(item["topic"] == "spray_paint_periodic_ticks" for item in unresolved)
    actions = json.loads((ROOT / "data/actions.json").read_text(encoding="utf-8"))
    missing = [
        item["id"]
        for item in actions
        if item.get("character_id") == "lynae"
        and float(item.get("damage_multiplier", 0.0) or 0.0) > 0.0
        and not item.get("source_status")
    ]
    assert not missing, missing
    print("lynae_excel_source_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
