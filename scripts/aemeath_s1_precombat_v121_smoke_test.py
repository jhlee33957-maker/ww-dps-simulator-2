from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import (
    ACCOUNT_SCOPE_ID,
    aemeath_s1_charged_sync_gain,
    aemeath_s1_heavy_crit_damage,
    initialize_account_constellation_state,
)


def main() -> None:
    chars = {"aemeath": {"sequence": 6, "constellation": {"sequence": 6}}}
    zero = initialize_account_constellation_state(chars, ACCOUNT_SCOPE_ID, 0)
    ready = initialize_account_constellation_state(chars, ACCOUNT_SCOPE_ID, 4.01)
    assert zero["aemeath"]["radiance_quick_charge_ready"] is False
    assert ready["aemeath"]["radiance_quick_charge_ready"] is True
    assert aemeath_s1_heavy_crit_damage(2.942, "aemeath_heavy_aemeath_charged_2", True) == 5.942
    assert aemeath_s1_heavy_crit_damage(2.942, "aemeath_heavy_mech_charged_2", True) == 5.942
    assert aemeath_s1_heavy_crit_damage(2.942, "aemeath_heavy_aemeath_charged_1", True) == 2.942
    assert aemeath_s1_heavy_crit_damage(2.942, "aemeath_human_heavy_attack", True) == 2.942
    assert aemeath_s1_heavy_crit_damage(2.942, "aemeath_heavy_mech_charged_2", False) == 2.942
    assert aemeath_s1_charged_sync_gain(True, True, "aemeath_heavy_aemeath_charged_2") == 100.0
    assert aemeath_s1_charged_sync_gain(True, True, "aemeath_heavy_mech_charged_2") == 100.0
    assert aemeath_s1_charged_sync_gain(True, True, "aemeath_heavy_mech_charged_1") == 0.0
    assert aemeath_s1_charged_sync_gain(False, True, "aemeath_heavy_mech_charged_2") == 0.0
    print("aemeath_s1_precombat_v121_smoke_test ok")


if __name__ == "__main__":
    main()
