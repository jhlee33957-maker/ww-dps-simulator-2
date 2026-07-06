from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


DATA_DIR = ROOT / "data"


def main() -> None:
    report = ROOT / "reports" / "weapon_effects_starfield_discord_note.md"
    extracted = DATA_DIR / "extracted" / "weapon_effects_starfield_discord_note.json"
    assert report.exists()
    assert extracted.exists()
    text = report.read_text(encoding="utf-8")
    data = json.loads(extracted.read_text(encoding="utf-8"))
    assert "metadata-only" in text
    assert data["static_stats_already_in_profile"] is True
    assert data["starfield_def_percent_passive_runtime_application"] == "metadata_only_already_in_profile"
    assert data["rank_tables"]["starfield_calibrator"]["1"]["concerto_restore_on_resonance_skill"] == 8.0
    assert data["rank_tables"]["starfield_calibrator"]["1"]["party_crit_damage_on_heal"] == 0.20
    assert data["rank_tables"]["discord"]["1"]["concerto_restore_on_resonance_skill"] == 8.0
    assert "resonance_skill_cast" in data["supported_trigger_event_names"]
    assert "party_stat_buff" in data["supported_effect_types"]
    assert data["source_status"] == "user_supplied_weapon_tooltip"
    assert data["weapon_effect_source_status"] == "user_supplied_weapon_tooltip"
    print("weapon_effect_metadata_smoke_test ok")


if __name__ == "__main__":
    main()
