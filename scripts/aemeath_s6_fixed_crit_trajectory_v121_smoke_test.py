from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import (
    aemeath_s6_fixed_crit_expected_multiplier,
    aemeath_s6_trajectory_gain,
)


def main() -> None:
    assert math.isclose(aemeath_s6_fixed_crit_expected_multiplier(0.80, 2.75), 2.4, abs_tol=1e-12)
    normal = aemeath_s6_trajectory_gain(0, base_gain=5, source="normal")
    assert normal["new_total"] == 5
    enhanced = aemeath_s6_trajectory_gain(normal["new_total"], base_gain=0, source="enhanced", enhanced_skill=True)
    assert enhanced["new_total"] == 15
    response = aemeath_s6_trajectory_gain(55, base_gain=1, source="normal", tune_response=True, fusion_application=True)
    assert response["base_gain_after_s6"] == 1
    assert response["extra_gain"] == 11
    assert response["new_total"] == 60
    print("aemeath_s6_fixed_crit_trajectory_v121_smoke_test ok")


if __name__ == "__main__":
    main()
