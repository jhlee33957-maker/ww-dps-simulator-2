from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.apply_direct_action_data_v61 as patcher


NORMAL_SOURCE = "\u89d2\u8272-\u5973!4120 / \u89d2\u8272\u6280\u80fd\u7c7b\u578b!533"
HIGH_SOURCE = "\u89d2\u8272-\u5973!4121 / \u89d2\u8272\u6280\u80fd\u7c7b\u578b!533"
TARGET_SCOPE = "host_action_actor_else_active_character"
OLD_TARGET_SCOPE = "active_character_at_trigger_time"


def main() -> None:
    manifest_bytes = (ROOT / "direct_action_data_patch_manifest_v61.json").read_bytes()
    source_bytes = (ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json").read_bytes()
    assert manifest_bytes == source_bytes
    manifest_hash = hashlib.sha256(source_bytes).hexdigest()
    assert manifest_hash == patcher.EXPECTED_MANIFEST_SHA256
    manifest = json.loads(source_bytes.decode("utf-8"))
    actions = json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))
    transitions = json.loads((ROOT / "data" / "transition_actions.json").read_text(encoding="utf-8"))
    policy_before = [row["id"] for row in actions if row.get("policy_selectable", True)]
    damaged = copy.deepcopy(actions)
    damaged_transitions = copy.deepcopy(transitions)
    for row in damaged:
        if row["id"] == "mornye_heavy_geopotential_shift":
            row.setdefault("mechanic_event_tags", []).append("team_heal")
            row["mechanic_effects"]["healing_proxy_implementation_status"] = "simplified_field_uptime_heal_proxy"
        if row["id"] in {"mornye_syntony_field_heal", "mornye_high_syntony_field_heal"}:
            row["mechanic_effects"]["target_scope"] = OLD_TARGET_SCOPE
        if row["id"] in {"mornye_heavy_geopotential_shift", "mornye_liberation_critical_protocol"}:
            row["mechanic_effects"]["scheduled_healing_target_scope"] = OLD_TARGET_SCOPE
    for row in damaged_transitions:
        if row["id"] == "mornye_intro_convergence":
            row["mechanic_effects"]["scheduled_healing_target_scope"] = OLD_TARGET_SCOPE
    restored, restored_transitions, changes, summary = patcher.apply_manifest_documents(
        manifest,
        damaged,
        damaged_transitions,
        manifest_hash=manifest_hash,
    )
    ids = {row["id"] for row in restored}
    assert {"mornye_syntony_field_heal", "mornye_high_syntony_field_heal"}.issubset(ids)
    restored_by_id = {row["id"]: row for row in restored}
    assert restored_by_id["mornye_syntony_field_heal"]["mechanic_effects"]["source_ref"] == NORMAL_SOURCE
    assert restored_by_id["mornye_high_syntony_field_heal"]["mechanic_effects"]["source_ref"] == HIGH_SOURCE
    assert restored_by_id["mornye_syntony_field_heal"]["mechanic_effects"]["target_scope"] == TARGET_SCOPE
    assert restored_by_id["mornye_high_syntony_field_heal"]["mechanic_effects"]["target_scope"] == TARGET_SCOPE
    assert restored_by_id["mornye_heavy_geopotential_shift"]["mechanic_effects"]["scheduled_healing_source_ref"] == NORMAL_SOURCE
    assert restored_by_id["mornye_liberation_critical_protocol"]["mechanic_effects"]["scheduled_healing_source_ref"] == HIGH_SOURCE
    assert restored_by_id["mornye_heavy_geopotential_shift"]["mechanic_effects"]["scheduled_healing_target_scope"] == TARGET_SCOPE
    assert restored_by_id["mornye_liberation_critical_protocol"]["mechanic_effects"]["scheduled_healing_target_scope"] == TARGET_SCOPE
    restored_transitions_by_id = {row["id"]: row for row in restored_transitions}
    assert (
        restored_transitions_by_id["mornye_intro_convergence"]["mechanic_effects"]["scheduled_healing_target_scope"]
        == TARGET_SCOPE
    )
    assert summary["policy_selectable_action_id_order_unchanged"] is True
    assert [row["id"] for row in restored if row.get("policy_selectable", True)] == policy_before
    _restored2, _transitions2, changes2, summary2 = patcher.apply_manifest_documents(
        manifest,
        copy.deepcopy(restored),
        copy.deepcopy(restored_transitions),
        manifest_hash=manifest_hash,
    )
    assert changes
    assert changes2 == []
    assert summary2["field_level_change_count"] == 0
    print("mornye_syntony_field_healing_manifest_reapply_smoke_test ok")


if __name__ == "__main__":
    main()
