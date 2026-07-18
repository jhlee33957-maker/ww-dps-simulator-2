from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import aemeath_s6_trajectory_gain


def main() -> None:
    party = aemeath_s6_trajectory_gain(0, base_gain=10, source="party_tune_response", tune_response=True)
    assert party["base_gain_after_s6"] == 10 and party["extra_gain"] == 10 and party["new_total"] == 20
    enhanced = aemeath_s6_trajectory_gain(0, base_gain=0, source="enhanced_skill", enhanced_skill=True)
    assert enhanced["new_total"] == 10
    fusion = aemeath_s6_trajectory_gain(0, base_gain=0, source="fusion_application", fusion_application=True)
    assert fusion["new_total"] == 1
    assert aemeath_s6_trajectory_gain(0, base_gain=5, source="normal")["new_total"] == 5
    print("aemeath_s6_no_generic_trajectory_double_v121_smoke_test ok")


if __name__ == "__main__":
    main()
