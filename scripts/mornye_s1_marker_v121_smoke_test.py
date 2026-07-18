from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import (
    mornye_dynamic_energy_regen_excess_amp,
    mornye_s1_marker_duration_seconds,
    mornye_s1_observation_marker_applies_interfered_marker,
)


def main() -> None:
    assert mornye_s1_marker_duration_seconds() == 20.0
    marker = mornye_s1_observation_marker_applies_interfered_marker()
    assert marker == {"observation_marker_applied": True, "interfered_marker_applied": True}
    assert mornye_dynamic_energy_regen_excess_amp(1.0) == 0.0
    assert mornye_dynamic_energy_regen_excess_amp(2.8) == 0.40
    print("mornye_s1_marker_v121_smoke_test ok")


if __name__ == "__main__":
    main()
