from __future__ import annotations

import json
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    runpy.run_path(str(ROOT / "scripts/lynae_source_audit.py"), run_name="__main__")
    records = json.loads((ROOT / "data/extracted/lynae_excel_action_map.json").read_text(encoding="utf-8"))
    by_id = {record["action_id"]: record for record in records}

    iridescent = by_id["lynae_iridescent_splash"]
    assert iridescent["mode_variant_rows"] == [2460, 2461]
    assert iridescent["calculation_type"] == "mutually_exclusive_mode_variants_same_multiplier"
    assert abs(iridescent["multiplier"] - 3.0418) < 1e-9
    assert abs(iridescent["multiplier"] - 6.0836) > 1e-9

    visual = by_id["lynae_visual_impact"]
    assert visual["mode_variant_rows"] == [2464, 2465]
    assert visual["calculation_type"] == "mutually_exclusive_mode_variants_same_multiplier"
    assert abs(visual["multiplier"] - 12.1672) < 1e-9
    assert abs(visual["multiplier"] - 24.3344) > 1e-9

    intro = by_id["lynae_intro_time_to_show_some_colors"]
    assert intro["mode_variant_rows"] == [2480, 2481]
    assert abs(intro["multiplier"] - 2.2480) < 1e-9
    assert abs(intro["multiplier"] - 0.4496) > 1e-9

    print("lynae_mode_variant_not_additive_smoke_test ok")


if __name__ == "__main__":
    main()
