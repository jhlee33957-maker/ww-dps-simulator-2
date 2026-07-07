from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BAD_FRAGMENTS = ["凉", "뷴", "뙑", "罌", "욃", "퉭"]


def main() -> None:
    path = ROOT / "data/mechanics/lynae_mechanics.json"
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    assert data["implemented_v2"]
    assert data["metadata_only_or_simplified"]
    assert data["source_references"]
    assert data["source_name"] == "琳奈"
    spectral = data["implemented_v2"]["spectral_analysis"]
    assert spectral["multiplier"] == 18.8075
    assert spectral["c2_implementation_status"] == "disabled_by_default_constellation"
    assert data["implemented_v2"]["visual_impact"]["party_tune_break_boost_points"] == 40
    assert data["metadata_only_or_simplified"]["spray_paint_periodic_ticks"] == "metadata_only_window_recorded"
    for fragment in BAD_FRAGMENTS:
        assert fragment not in text
    print("lynae_mechanics_reference_smoke_test ok")


if __name__ == "__main__":
    main()
