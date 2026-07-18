from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import (
    aemeath_s2_skill_multiplier,
    aemeath_s2_tune_sequential_multipliers,
)


def main() -> None:
    assert aemeath_s2_skill_multiplier(3.0, enhanced=True) == 6.0
    assert aemeath_s2_skill_multiplier(3.0, enhanced=True, mechanic_packet=True) == 3.0
    result = aemeath_s2_tune_sequential_multipliers(hit_count=5)
    assert result["per_hit_final_damage_bonuses"] == [0.0, 0.2, 0.4, 0.6, 0.8]
    assert result["final_stacks"] == 5
    assert math.isclose(result["aggregate_equivalent_multiplier"], 1.4, abs_tol=1e-12)
    refresh = aemeath_s2_tune_sequential_multipliers(hit_count=2, existing_stacks=4)
    assert refresh["per_hit_final_damage_bonuses"] == [0.8, 1.0]
    assert refresh["final_stacks"] == 5
    print("aemeath_s2_sequential_hit_v121_smoke_test ok")


if __name__ == "__main__":
    main()
