from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import (
    ACCOUNT_SCOPE_ID,
    initialize_account_constellation_state,
    lynae_s1_light_leap_multiplier,
    lynae_s1_paint_schedule,
    lynae_s1_precombat_overflow,
)


def main() -> None:
    schedule = lynae_s1_paint_schedule()
    assert schedule["duration_frames"] == 600
    assert schedule["application_tick_frames"] == [1, 121, 241, 361, 481]
    assert schedule["endpoint_tick_excluded"] is True
    assert schedule["pull_diagnostic_tick_frames"] == [360]
    assert schedule["pull_runtime_effect"] == 0.0
    assert lynae_s1_light_leap_multiplier(2.0) == 3.2
    assert lynae_s1_precombat_overflow(2.0, True) == 0.0
    assert lynae_s1_precombat_overflow(2.01, True) == 120.0
    state = initialize_account_constellation_state({"lynae": {"sequence": 2}}, ACCOUNT_SCOPE_ID, 2.01, optical_sampling_active=True)
    assert state["lynae"]["overflow_restored_precombat"] == 120.0
    print("lynae_s1_paint_precombat_v121_smoke_test ok")


if __name__ == "__main__":
    main()
