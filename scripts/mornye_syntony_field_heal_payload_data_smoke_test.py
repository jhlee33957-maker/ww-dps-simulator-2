from __future__ import annotations

import json

from mornye_syntony_field_heal_test_helpers import DATA_DIR, NORMAL_FRAMES


NORMAL_SOURCE = "角色-女!4120 / 角色技能类型!533"
HIGH_SOURCE = "角色-女!4121 / 角色技能类型!533"
TARGET_SCOPE = "host_action_actor_else_active_character"


def assert_payload(record: dict, *, action_id: str, source_ref: str, multiplier: float) -> None:
    assert record["id"] == action_id
    assert record["policy_selectable"] is False
    assert record["scheduled_event_type"] == "healing"
    assert record["hits"] == []
    assert record["damage_multiplier"] == 0.0
    assert record["tune_break_multiplier"] == 0.0
    assert record["off_tune_value"] == 0.0
    assert record["resonance_energy_gain"] == 0.0
    assert record["concerto_energy_gain"] == 0.0
    assert record["cooldown"] == 0
    effects = record["mechanic_effects"]
    assert effects["payload_event_type"] == "healing"
    assert effects["source_status"] == "workbook_confirmed_scheduled_heal"
    assert effects["source_ref"] == source_ref
    assert effects["relative_tick_frames"] == NORMAL_FRAMES
    assert effects["target_scope"] == TARGET_SCOPE
    healing = effects["healing_metadata"]
    assert healing["base_heal"] == 1805.0
    assert healing["scaling_stat"] == "def"
    assert healing["scaling_multiplier"] == 0.945
    assert healing["field_healing_multiplier"] == multiplier
    assert healing["healing_bonus_applied"] == 0.0
    assert healing["healing_bonus_source_status"] == "metadata_only_not_applied"


def main() -> None:
    actions = json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8"))
    policy_order = [row["id"] for row in actions if row.get("policy_selectable", True)]
    by_id = {row["id"]: row for row in actions}
    assert_payload(
        by_id["mornye_syntony_field_heal"],
        action_id="mornye_syntony_field_heal",
        source_ref=NORMAL_SOURCE,
        multiplier=1.0,
    )
    assert_payload(
        by_id["mornye_high_syntony_field_heal"],
        action_id="mornye_high_syntony_field_heal",
        source_ref=HIGH_SOURCE,
        multiplier=1.4,
    )
    assert "mornye_syntony_field_heal" not in policy_order
    assert "mornye_high_syntony_field_heal" not in policy_order
    assert by_id["mornye_heavy_geopotential_shift"].get("mechanic_event_tags", []) == []
    assert by_id["mornye_liberation_critical_protocol"].get("mechanic_event_tags", []) == []
    print("mornye_syntony_field_heal_payload_data_smoke_test ok")


if __name__ == "__main__":
    main()
