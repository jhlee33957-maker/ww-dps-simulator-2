from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.build_profiles import load_build_profiles


DATA_DIR = ROOT / "data"


def main() -> None:
    profiles = load_build_profiles(DATA_DIR)["profiles"]

    aemeath = profiles["aemeath"]["aemeath_account_actual_01"]["weapon"]
    lynae = profiles["lynae"]["lynae_account_actual_01"]["weapon"]
    mornye = profiles["mornye"]["mornye_account_actual_01"]["weapon"]
    benchmark_mornye = profiles["mornye"]["mornye_user_real_01"]["weapon"]

    assert aemeath["weapon_id"] == "everbright_polestar" and aemeath["rank"] == 1
    assert lynae["weapon_id"] == "static_mist" and lynae["rank"] == 5
    assert mornye["weapon_id"] == "starfield_calibrator" and mornye["display_name"] == "Starfield Calibrator"
    assert mornye["rank"] == 5

    assert benchmark_mornye["weapon_id"] == "discord"
    assert benchmark_mornye["rank"] == 5

    party = json.loads((DATA_DIR / "party_presets.json").read_text(encoding="utf-8-sig"))
    assert not any(item["party_id"].startswith("account_") for item in party)
    assert not any("account_actual" in json.dumps(item) for item in party)

    print("user_account_actual_v120_weapon_loadout_smoke_test ok")


if __name__ == "__main__":
    main()
