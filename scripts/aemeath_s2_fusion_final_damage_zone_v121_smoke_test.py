from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import aemeath_s2_fusion_final_damage_multiplier


def main() -> None:
    for stacks in (0, 1, 10, 30, 60):
        result = aemeath_s2_fusion_final_damage_multiplier(removed_trajectory_count=stacks, enhancement_state=True)
        assert result["final_damage_increase"] == 4.0 + 0.15 * stacks
        assert result["final_damage_multiplier"] == 5.0 + 0.15 * stacks
    assert aemeath_s2_fusion_final_damage_multiplier(removed_trajectory_count=10, enhancement_state=True)["final_damage_multiplier"] == 6.5
    print("aemeath_s2_fusion_final_damage_zone_v121_smoke_test ok")


if __name__ == "__main__":
    main()
