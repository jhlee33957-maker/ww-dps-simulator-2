from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    halo_md = ROOT / "reports" / "mornye_halo_of_starry_radiance_5set_runtime_buff_note.md"
    halo_json = ROOT / "data" / "extracted" / "mornye_halo_of_starry_radiance_5set_runtime_buff_note.json"
    off_tune_md = ROOT / "reports" / "mornye_off_tune_buildup_rate_source_note.md"
    off_tune_json = ROOT / "data" / "extracted" / "mornye_off_tune_buildup_rate_source_note.json"
    for path in (halo_md, halo_json, off_tune_md, off_tune_json):
        assert path.exists(), f"Missing metadata artifact: {path}"

    halo = read_json(halo_json)
    off_tune = read_json(off_tune_json)
    assert halo["trigger_event_tags"] == ["team_heal"]
    assert halo["formula"] == "min(current_off_tune_buildup_rate * 0.20, 0.25)"
    assert halo["trigger_damage_receives_buff"] is True
    assert halo["field_creation_damage_receives_buff"] is True
    assert halo["implementation_timing_mode"] == "same_action_field_creation_approximation"
    assert "corrected" in halo["obsolete_previous_timing_rule"]
    assert halo["examples"]["base_1_0"] == 0.2
    assert halo["examples"]["syntony_field_1_5"] == 0.25
    assert "exact healing amount" in halo["unsupported"]
    assert "exact heal tick timing" in halo["unsupported"]

    assert off_tune["default_off_tune_buildup_rate"] == 1.0
    assert off_tune["syntony_field_off_tune_bonus"] == 0.5
    assert off_tune["c2_additional_bonus"] == 0.2
    assert off_tune["c2_default_active"] is False
    assert off_tune["field_creation_off_tune_applies_before_halo_value"] is True
    assert off_tune["implementation_timing_mode"] == "same_action_field_creation_approximation"
    assert off_tune["energy_regen_is_not_off_tune_buildup_rate"] is True
    print("mornye_halo_of_starry_radiance_5set_metadata_smoke_test ok")


if __name__ == "__main__":
    main()
