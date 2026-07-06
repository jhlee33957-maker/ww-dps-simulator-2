from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "weapon_effects_everbright_polestar_note.md"
JSON_PATH = ROOT / "data" / "extracted" / "weapon_effects_everbright_polestar_note.json"


def main() -> None:
    assert REPORT_PATH.exists(), f"Missing report: {REPORT_PATH}"
    assert JSON_PATH.exists(), f"Missing JSON report: {JSON_PATH}"
    report = REPORT_PATH.read_text(encoding="utf-8")
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    assert data["weapon_id"] == "everbright_polestar"
    assert data["source_status"] == "user_supplied_weapon_tooltip"
    assert data["static_stats_already_in_profile"] is True
    assert data["base_atk_and_crit_already_in_profile"] is True
    assert data["affected_profile_ids"] == ["aemeath_user_real_01"]
    assert set(data["trigger_events"]) == {"tune_rupture_shifting", "fusion_burst"}
    assert "tune_break_formula_damage" in data["not_applied_to"]
    assert "tune_response_formula_damage" in data["not_applied_to"]
    assert "DEF Multiplier" in data["formula_integration"]["def_ignore"]
    assert "RES Multiplier" in data["formula_integration"]["fusion_res_ignore"]
    assert data["rank_table"]["1"]["all_attribute_damage_bonus"] == 0.12
    assert data["rank_table"]["5"]["resonance_liberation_def_ignore"] == 0.64

    for expected in (
        "Everbright Polestar",
        "Weapon base ATK and crit stat are assumed already reflected",
        "Tune Break",
        "Tune Response",
        "DEF Multiplier",
        "RES Multiplier",
        "user_supplied_weapon_tooltip",
    ):
        assert expected in report

    print("everbright_polestar_metadata_smoke_test ok")


if __name__ == "__main__":
    main()
