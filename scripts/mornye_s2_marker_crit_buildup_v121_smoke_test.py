from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import mornye_s2_field_off_tune_efficiency, mornye_s2_marker_crit_damage


def main() -> None:
    assert mornye_s2_marker_crit_damage(1.0) == 0.0
    assert mornye_s2_marker_crit_damage(2.7944) == 0.32
    assert mornye_s2_field_off_tune_efficiency() == 0.70
    print("mornye_s2_marker_crit_buildup_v121_smoke_test ok")


if __name__ == "__main__":
    main()
