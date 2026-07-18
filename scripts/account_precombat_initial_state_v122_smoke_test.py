from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_party_v122_test_utils import PARTY_ID
from validate_account_party_v122 import dry_validate_account_party


def main() -> None:
    result = dry_validate_account_party(ROOT, PARTY_ID)
    assert result["initial_active_character"] == "mornye"
    assert result["profiles"]["aemeath"]["sequence"] == 6
    assert result["profiles"]["lynae"]["sequence"] == 2
    assert result["profiles"]["mornye"] == {
        "profile_id": "mornye_account_actual_01",
        "weapon_id": "starfield_calibrator",
        "weapon_rank": 5,
        "sequence": 3,
    }
    assert result["aemeath_resonance_mode"] == "tune_rupture"
    assert result["precombat_elapsed_seconds"] == 4.01
    assert result["aemeath_radiance_quick_charge_ready"] is True
    assert result["lynae_optical_sampling_active"] is True
    assert result["lynae_overflow_initial_gain"] == 120
    assert result["combat_time"] == result["current_elapsed_action_time"] == 0.0
    print("account_precombat_initial_state_v122_smoke_test ok")


if __name__ == "__main__":
    main()
