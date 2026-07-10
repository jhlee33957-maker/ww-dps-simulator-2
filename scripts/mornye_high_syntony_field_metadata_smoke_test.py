from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


DATA_DIR = ROOT / "data"


def test_high_syntony_metadata_files() -> None:
    report_path = ROOT / "reports" / "mornye_high_syntony_field_runtime_buff_note.md"
    note_path = DATA_DIR / "extracted" / "mornye_high_syntony_field_runtime_buff_note.json"
    assert report_path.exists()
    assert note_path.exists()

    report = report_path.read_text(encoding="utf-8")
    for phrase in (
        "Critical Protocol can create High Syntony Field",
        "party DEF +20%",
        "inherits Syntony Field's Off-Tune",
        "simplified field uptime",
        "same_action_high_syntony_field_creation_approximation",
        "Halo ATK% does not increase Mornye DEF-scaling damage",
        "Energy Regen remains separate",
        "Automatic Syntony/High Syntony field damage scheduling",
    ):
        assert phrase in report

    note = json.loads(note_path.read_text(encoding="utf-8"))
    assert note["character_id"] == "mornye"
    assert note["action_id"] == "mornye_liberation_critical_protocol"
    assert note["field_id"] == "high_syntony_field"
    assert note["duration_seconds"] == 25.0
    assert note["def_percent_bonus"] == 0.2
    assert note["off_tune_buildup_rate_inherited_bonus"] == 0.5
    assert note["healing_inherited"] is True
    assert note["healing_multiplier_bonus"] == 0.4
    assert note["exact_healing_amount_modeled"] is False
    assert note["exact_heal_tick_timing_modeled"] is False
    assert note["implementation_timing_mode"] == "same_action_high_syntony_field_creation_approximation"
    assert note["high_syntony_field_requires_active_syntony_field"] is True
    assert "full_tune_break_interfered_system" in note["unsupported_followup_mechanics"]
    assert any(ref.get("cell") == "D4124" for ref in note["source_references"])
    assert any(ref.get("source_status") == "user_supplied_skill_screenshot_not_embedded" for ref in note["source_references"])


def test_related_metadata_updated() -> None:
    off_tune = json.loads((DATA_DIR / "extracted" / "mornye_off_tune_buildup_rate_source_note.json").read_text(encoding="utf-8"))
    assert off_tune["high_syntony_field_off_tune_inheritance_status"] == "implemented_simplified_inheritance"
    assert off_tune["high_syntony_field_off_tune_inherited_bonus"] == 0.5
    assert off_tune["energy_regen_is_not_off_tune_buildup_rate"] is True

    halo = json.loads(
        (DATA_DIR / "extracted" / "mornye_halo_of_starry_radiance_5set_runtime_buff_note.json").read_text(
            encoding="utf-8"
        )
    )
    assert halo["high_syntony_field_support"]["off_tune_inheritance_status"] == "implemented_simplified_inheritance"
    assert halo["high_syntony_field_support"]["heal_proxy_inheritance_status"] == "implemented_simplified_field_uptime_proxy"
    assert halo["high_syntony_field_support"]["halo_atk_buff_does_not_affect_mornye_def_damage"] is True

    mechanics = json.loads((DATA_DIR / "mechanics" / "mornye_mechanics.json").read_text(encoding="utf-8"))
    high_state = next(item for item in mechanics["states"] if item["state"] == "high_syntony_field")
    assert high_state["implemented"] == "implemented_simplified_runtime_support"
    assert "inherited Off-Tune +50%" in high_state["notes"]
    high_field = next(item for item in mechanics["syntony_field"] if item["field"] == "High Syntony Field")
    assert "inherits party off_tune_buildup_rate +0.5" in high_field["effects"]


def main() -> None:
    test_high_syntony_metadata_files()
    test_related_metadata_updated()
    print("mornye_high_syntony_field_metadata_smoke_test ok")


if __name__ == "__main__":
    main()
