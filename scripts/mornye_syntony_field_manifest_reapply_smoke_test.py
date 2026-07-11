from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.apply_direct_action_data_v61 import apply_manifest_documents


DATA_DIR = ROOT / "data"


def old_five_hit_payload() -> dict:
    return {
        "id": "mornye_syntony_field_damage",
        "name": "Mornye Syntony Field Damage",
        "character_id": "mornye",
        "action_type": "resonance_liberation",
        "duration": 2.0,
        "action_time": 2.0,
        "combat_time_cost": 2.0,
        "cooldown": 0,
        "resonance_energy_gain": 0,
        "concerto_energy_gain": 0,
        "resonance_energy_cost": 0,
        "hits": [
            {"time": 0.45, "damage_multiplier": 0.3977, "tags": ["fusion", "field", "resonance_liberation"], "name": "Syntony Field hit 1"},
            {"time": 0.9, "damage_multiplier": 0.3977, "tags": ["fusion", "field", "resonance_liberation"], "name": "Syntony Field hit 2"},
            {"time": 1.35, "damage_multiplier": 0.3977, "tags": ["fusion", "field", "resonance_liberation"], "name": "Syntony Field hit 3"},
            {"time": 1.8, "damage_multiplier": 0.3977, "tags": ["fusion", "field", "resonance_liberation"], "name": "Syntony Field hit 4"},
            {"time": 2.0, "damage_multiplier": 0.3977, "tags": ["fusion", "field", "resonance_liberation"], "name": "Syntony Field hit 5"},
        ],
        "tags": ["fusion", "field", "resonance_liberation", "mornye", "metadata_optional"],
        "policy_selectable": False,
        "data_status": "review_optional_v1",
        "notes": "Old fabricated five-hit placeholder.",
        "scaling_stat": "def",
        "off_tune_value": 66.4,
        "off_tune_value_source_status": "workbook_confirmed",
        "off_tune_value_source_ref": "old",
    }


def main() -> None:
    manifest = json.loads((DATA_DIR / "source" / "direct_action_data_patch_manifest_v61.json").read_text(encoding="utf-8"))
    actions = json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8"))
    transitions = json.loads((DATA_DIR / "transition_actions.json").read_text(encoding="utf-8"))
    policy_before = [record["id"] for record in actions if record.get("policy_selectable", True)]

    damage_index = next(index for index, record in enumerate(actions) if record["id"] == "mornye_syntony_field_damage")
    actions[damage_index] = old_five_hit_payload()
    actions = [record for record in actions if record["id"] != "mornye_syntony_field_target_damage"]

    repaired_actions, repaired_transitions, changes, summary = apply_manifest_documents(
        manifest,
        copy.deepcopy(actions),
        copy.deepcopy(transitions),
        manifest_hash="manifest_reapply_smoke_test",
    )
    assert summary["declared_non_policy_action_ids_added"] == ["mornye_syntony_field_target_damage"]
    assert summary["policy_selectable_action_id_order_unchanged"] is True
    assert [record["id"] for record in repaired_actions if record.get("policy_selectable", True)] == policy_before
    assert len(changes) == 2

    records = {record["id"]: record for record in repaired_actions}
    assert len(records["mornye_syntony_field_damage"]["hits"]) == 1
    assert records["mornye_syntony_field_damage"]["off_tune_value"] == 0.0
    assert records["mornye_syntony_field_target_damage"]["hits"][0]["damage_multiplier"] == 0.9902

    _again_actions, _again_transitions, second_changes, second_summary = apply_manifest_documents(
        manifest,
        copy.deepcopy(repaired_actions),
        copy.deepcopy(repaired_transitions),
        manifest_hash="manifest_reapply_smoke_test",
    )
    assert second_changes == []
    assert second_summary["declared_non_policy_action_ids_added"] == []
    assert second_summary["policy_selectable_action_id_order_unchanged"] is True

    print("mornye_syntony_field_manifest_reapply_smoke_test ok")


if __name__ == "__main__":
    main()
