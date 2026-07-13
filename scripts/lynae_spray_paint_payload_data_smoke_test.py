from __future__ import annotations

import json
from pathlib import Path

from lynae_spray_paint_test_helpers import (
    TUNE_RUPTURE_REF,
    TUNE_STRAIN_REF,
    assert_canonical_source_refs,
)


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ID = "lynae_spray_paint_flux_application"


def main() -> None:
    assert_canonical_source_refs()
    actions = json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))
    by_id = {record["id"]: record for record in actions}
    payload = by_id[PAYLOAD_ID]
    assert payload["policy_selectable"] is False
    assert payload["scheduled_event_type"] == "status_application"
    assert payload["hits"] == []
    assert payload["damage_multiplier"] == 0.0
    assert payload["tune_break_multiplier"] == 0.0
    assert payload["off_tune_value"] == 0.0
    assert payload["resonance_energy_gain"] == 0.0
    assert payload["concerto_energy_gain"] == 0.0
    assert payload["cooldown"] == 0.0
    assert payload["mechanic_effects"]["scheduled_status_effect_id"] == "lynae_photocromic_flux"

    visual = by_id["lynae_visual_impact"]
    schedule = visual["mechanic_effects"]["spray_paint_status_schedule"]
    assert schedule["payload_action_id"] == PAYLOAD_ID
    assert schedule["payload_event_type"] == "status_application"
    assert schedule["first_check_frames"] == 1
    assert schedule["check_interval_frames"] == 120
    assert schedule["field_duration_frames"] == 300
    assert schedule["relative_application_frames"] == [1, 121, 241]
    assert schedule["max_application_count"] == 3
    assert schedule["remove_on_max_trigger_count"] is False
    assert schedule["target_presence_assumption"] == "single_target_remains_inside_paint_area"
    assert schedule["mode_mapping"]["tune_strain"]["source_row"] == TUNE_STRAIN_REF
    assert schedule["mode_mapping"]["tune_rupture"]["source_row"] == TUNE_RUPTURE_REF
    print("lynae_spray_paint_payload_data_smoke_test ok")


if __name__ == "__main__":
    main()
