from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONTRACT = ROOT / "data" / "source" / "user_account_actual_v120.json"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-9) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tol), f"{label}: {actual} != {expected}"


def main() -> None:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert data["schema_version"]
    assert data["source_status"] == "user_screenshot_and_user_confirmation"
    assert data["confirmed_at_candidate"] == 120
    assert data["simulation_status"] == "blocked_pending_constellation_mechanics"

    expected_sequences = {"aemeath": 6, "lynae": 2, "mornye": 3}
    for character_id, sequence in expected_sequences.items():
        entry = data["constellation_metadata"][character_id]
        assert entry == {"sequence": sequence, "mechanics_implemented": False}

    blockers = set(data["blockers"])
    for expected in [
        "Aemeath S1-S6 mechanics not yet source-audited and implemented",
        "Lynae S1-S2 mechanics not yet source-audited and implemented",
        "Mornye S1-S3 mechanics not yet source-audited and implemented",
        "account baseline not established",
        "account BC/PPO not regenerated",
        "account search not executed",
    ]:
        assert expected in blockers
    assert "simulation, training, evaluation, and search are rejected" in data["explicit_rule"]

    aemeath = data["profiles"]["aemeath_account_actual_01"]
    assert aemeath["sequence"] == 6 and aemeath["simulation_ready"] is False
    assert aemeath["equipment"] == {
        "weapon_id": "everbright_polestar",
        "weapon_rank": 1,
        "main_echo": "sigillum",
        "echo_set": "Trailblazing Star 5pc",
    }
    assert aemeath["account_display_stats"] == {
        "hp": 15585,
        "atk": 2657,
        "def": 1148,
        "energy_regen": 1.2,
        "crit_rate": 0.832,
        "crit_damage": 2.942,
    }
    assert_close(aemeath["stat_components"]["atk"]["calculated_static_value"], 2657.584, "Aemeath ATK")
    assert_close(aemeath["damage_bonuses"]["resonance_liberation"], 0.688, "Aemeath Liberation")
    assert_close(aemeath["bonus_decomposition"]["fusion"]["static_profile_total"], 0.40, "Aemeath static Fusion")
    assert_close(aemeath["bonus_decomposition"]["fusion"]["everbright_polestar_r1_runtime_all_attribute_bonus"], 0.12, "Aemeath weapon runtime")

    lynae = data["profiles"]["lynae_account_actual_01"]
    assert lynae["sequence"] == 2 and lynae["simulation_ready"] is False
    assert lynae["equipment"]["weapon_id"] == "static_mist"
    assert lynae["equipment"]["weapon_rank"] == 5
    assert_close(lynae["account_display_stats"]["energy_regen"], 1.548, "Lynae ER")
    assert_close(lynae["stat_components"]["atk"]["calculated_static_value"], 1929.758, "Lynae ATK")
    assert_close(lynae["damage_bonuses"]["spectro"], 0.700, "Lynae Spectro")

    mornye = data["profiles"]["mornye_account_actual_01"]
    assert mornye["sequence"] == 3 and mornye["simulation_ready"] is False
    assert mornye["equipment"]["weapon_id"] == "starfield_calibrator"
    assert mornye["equipment"]["display_name"] == "Starfield Calibrator"
    assert mornye["equipment"]["weapon_rank"] == 5
    assert_close(mornye["account_display_stats"]["energy_regen"], 2.7944, "Mornye ER")
    assert_close(mornye["stat_components"]["atk"]["calculated_static_value"], 1158.629, "Mornye ATK")
    assert_close(mornye["stat_components"]["def"]["calculated_static_value"], 3357.1385, "Mornye DEF")

    print("user_account_actual_v120_source_contract_smoke_test ok")


if __name__ == "__main__":
    main()
