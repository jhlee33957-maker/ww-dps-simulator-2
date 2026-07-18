from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.roster import read_party_presets

PARTY_ID = "aemeath_mornye_lynae_account_actual_01"


def main() -> None:
    party = read_party_presets(ROOT / "data")[PARTY_ID]
    assert party["members"] == ["mornye", "aemeath", "lynae"]
    assert party["initial_active"] == "mornye"
    assert party["build_profiles"] == {
        "mornye": "mornye_account_actual_01",
        "aemeath": "aemeath_account_actual_01",
        "lynae": "lynae_account_actual_01",
    }
    assert party["account_scope"]["scope_id"] == "single_persistent_boss_no_kill_no_survival"
    assert party["mechanic_overrides"]["aemeath"] == {
        "aemeath_resonance_mode": "tune_rupture",
        "aemeath_resonance_mode_source": "user_confirmed_account_party_v122",
    }
    assert party["mechanic_overrides"]["lynae"]["lynae_constellation"] == 2
    assert party["mechanic_overrides"]["lynae"]["spectral_analysis_enabled"] is True
    assert party["mechanic_overrides"]["mornye"]["mornye_heal_event_mode"] == "scheduled_180f_exact"
    tune_break = party["mechanic_overrides"]["tune_break_system"]
    assert tune_break["mode"] == "excel_off_tune_mistune_action"
    assert tune_break["enemy_off_tune_max"] == 3920
    assert tune_break["enemy_tune_break_cooldown_seconds"] == 3.0
    assert party["generic_swap"]["action_time"] == party["generic_swap"]["combat_time_cost"] == 0.0
    print("account_party_v122_contract_smoke_test ok")


if __name__ == "__main__":
    main()
