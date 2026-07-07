from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.roster import read_party_presets


NEW_PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
BASELINE_PARTY_ID = "aemeath_mornye_enabled_test_party"


def main() -> None:
    presets = read_party_presets(ROOT / "data")
    assert NEW_PARTY_ID in presets
    assert BASELINE_PARTY_ID in presets
    baseline = presets[BASELINE_PARTY_ID]
    preset = presets[NEW_PARTY_ID]

    expected_members = ["lynae" if member == "dummy_sub_dps" else member for member in baseline["members"]]
    assert preset["members"] == expected_members
    assert preset["members"] == ["mornye", "aemeath", "lynae"]
    assert "dummy_sub_dps" not in preset["members"]
    assert preset["initial_active"] == baseline["initial_active"]
    assert preset["build_profiles"] == {
        "mornye": "mornye_user_real_01",
        "aemeath": "aemeath_user_real_01",
        "lynae": "lynae_user_real_01",
    }
    print("aemeath_mornye_lynae_party_preset_smoke_test ok")


if __name__ == "__main__":
    main()
