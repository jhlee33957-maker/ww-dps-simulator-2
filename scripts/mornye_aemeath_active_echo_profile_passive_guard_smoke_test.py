from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    profiles = json.loads((ROOT / "data" / "build_profiles.json").read_text(encoding="utf-8-sig"))["profiles"]
    mornye = profiles["mornye"]["mornye_user_real_01"]
    aemeath = profiles["aemeath"]["aemeath_user_real_01"]

    assert mornye["main_echo_id"] == "reactor_husk"
    assert mornye["static_energy_regen_bonus"] == 0.10
    assert mornye["static_energy_regen_already_in_profile"] is True
    assert mornye["runtime_passive_enabled"] is False
    assert mornye["combat_stats"]["energy_regen"] == 2.5424
    assert mornye["damage_bonuses"]["by_category"]["echo_ability"] == 0.0

    assert aemeath["main_echo_id"] == "sigillum"
    assert aemeath["static_resonance_liberation_damage_bonus"] == 0.25
    assert aemeath["static_resonance_liberation_bonus_already_in_profile"] is True
    assert aemeath["runtime_passive_enabled"] is False
    assert aemeath["damage_bonuses"]["by_category"]["resonance_liberation"] == 0.688
    assert aemeath["damage_bonuses"]["by_category"]["echo_ability"] == 0.0
    print("mornye_aemeath_active_echo_profile_passive_guard_smoke_test ok")


if __name__ == "__main__":
    main()
