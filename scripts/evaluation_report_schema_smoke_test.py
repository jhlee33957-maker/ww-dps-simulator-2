from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.evaluation_report import add_generated_damage_summary


OLD_SUMMARY_KEYS = (
    "total_damage",
    "dps",
    "damage_by_category",
    "damage_by_selected_action",
    "damage_by_resolved_action",
)

NEW_SUMMARY_KEYS = (
    "generated_mechanic_damage_total",
    "generated_mechanic_damage_action_count",
    "generated_mechanic_damage_share_of_total",
    "aemeath_forte_generated_damage_total",
    "aemeath_seraphic_duet_followup_damage_total",
    "aemeath_seraphic_duet_followup_normal_count",
    "aemeath_seraphic_duet_followup_enhanced_count",
    "damage_by_action_damage_category",
    "damage_by_hit_formula_type",
    "damage_by_generated_mechanic_source",
    "damage_by_character_and_source",
    "report_generation_version",
    "timeline_schema_has_generated_damage_fields",
    "summary_schema_has_generated_damage_fields",
    "generated_damage_reporting_status",
    "legacy_damage_by_source_action_category",
    "direct_damage_by_category",
    "direct_damage_by_damage_bonus_category",
    "generated_damage_by_source_action_category",
    "effective_damage_role_breakdown",
    "basic_attack_direct_damage_share_of_total",
    "resonance_liberation_direct_damage_share_of_total",
)


def main() -> None:
    base_payload = {
        "total_damage": 1000.0,
        "dps": 1000.0,
        "damage_by_category": {"basic_attack": 1000.0},
        "damage_by_selected_action": {"aemeath_seraphic_duet_overturn": 1000.0},
        "damage_by_resolved_action": {"aemeath_seraphic_duet_overturn": 1000.0},
    }
    timeline = [
        {
            "character_id": "aemeath",
            "actor_character_id": "aemeath",
            "damage_category": "resonance_skill",
            "damage_bonus_category": "resonance_liberation",
            "normal_damage": 600.0,
            "total_action_damage": 1000.0,
            "generated_mechanic_damage": 400.0,
            "aemeath_forte_generated_damage": 400.0,
            "aemeath_seraphic_duet_followup_triggered": True,
            "aemeath_seraphic_duet_followup_variant": "normal",
            "aemeath_seraphic_duet_followup_damage": 400.0,
            "aemeath_seraphic_duet_followup_repeat_count": 5,
            "aemeath_seraphic_duet_followup_multiplier": 1.0935,
        }
    ]
    generated_payload = add_generated_damage_summary(
        base_payload,
        timeline,
        total_damage=base_payload["total_damage"],
    )
    for key in OLD_SUMMARY_KEYS:
        assert key in generated_payload, f"old summary key removed: {key}"
    for key in NEW_SUMMARY_KEYS:
        assert key in generated_payload, f"new generated summary key missing: {key}"
    assert generated_payload["generated_mechanic_damage_total"] == 400.0
    assert generated_payload["generated_mechanic_damage_share_of_total"] == 0.4
    assert generated_payload["aemeath_seraphic_duet_followup_normal_count"] == 1
    assert generated_payload["aemeath_seraphic_duet_followup_enhanced_count"] == 0
    assert generated_payload["report_generation_version"] == "generated_damage_reporting_v2"
    assert generated_payload["timeline_schema_has_generated_damage_fields"] is True
    assert generated_payload["summary_schema_has_generated_damage_fields"] is True
    assert generated_payload["generated_damage_reporting_status"] == "ok"
    assert generated_payload["direct_damage_by_category"]["resonance_skill"] == 600.0
    assert generated_payload["legacy_damage_by_source_action_category"]["resonance_skill"] == 1000.0
    assert generated_payload["generated_damage_by_source_action_category"]["resonance_skill"] == 400.0
    assert generated_payload["effective_damage_role_breakdown"]["total_damage_check"] == 1000.0

    with tempfile.TemporaryDirectory() as tmpdir:
        summary_path = Path(tmpdir) / "ppo_evaluation_summary.json"
        summary_path.write_text(json.dumps(generated_payload, indent=2), encoding="utf-8")
        loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded["generated_mechanic_damage_total"] == 400.0

    missing_field_payload = add_generated_damage_summary(
        base_payload,
        [{"character_id": "aemeath", "total_action_damage": 0.0}],
        total_damage=0.0,
    )
    assert missing_field_payload["generated_mechanic_damage_total"] == 0.0
    assert missing_field_payload["aemeath_forte_generated_damage_total"] == 0.0
    assert missing_field_payload["generated_mechanic_damage_share_of_total"] == 0.0
    assert missing_field_payload["generated_damage_reporting_status"] == "no_generated_damage_fields_in_timeline"
    assert missing_field_payload["damage_by_generated_mechanic_source"]["aemeath_forte"] == 0.0
    print("evaluation_report_schema_smoke_test ok")


if __name__ == "__main__":
    main()
