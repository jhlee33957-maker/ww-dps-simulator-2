from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import aemeath_s3_register_contributor, aemeath_s3_reset_for_mode_switch


def main() -> None:
    state = {"aemeath": {"sequence": 6}}
    for character_id in ("aemeath", "mornye", "lynae"):
        result = aemeath_s3_register_contributor(state, "tune_rupture", character_id)
    assert result["contributors"] == ["aemeath", "mornye", "lynae"]
    assert math.isclose(result["crit_damage_bonus"], 0.60, abs_tol=1e-12)
    assert result["finale_deepen"] == 0.25
    aemeath_s3_reset_for_mode_switch(state, "fusion_burst")
    assert state["aemeath"]["s3_tune_contributors"] == []
    first = aemeath_s3_register_contributor(state, "fusion_burst", "aemeath")
    second = aemeath_s3_register_contributor(state, "fusion_burst", "mornye")
    assert first["crit_damage_bonus"] == 0.30
    assert second["crit_damage_bonus"] == 0.60
    print("aemeath_s3_contributor_v121_smoke_test ok")


if __name__ == "__main__":
    main()
