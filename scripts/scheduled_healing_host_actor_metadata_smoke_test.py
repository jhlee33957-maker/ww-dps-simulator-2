from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.apply_direct_action_data_v61 as patcher

TARGET_SCOPE = "host_action_actor_else_active_character"
PAYLOAD_IDS = {"mornye_syntony_field_heal", "mornye_high_syntony_field_heal"}


def main() -> None:
    actions = json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in actions}
    for action_id in PAYLOAD_IDS:
        assert by_id[action_id]["mechanic_effects"]["target_scope"] == TARGET_SCOPE

    assert (
        by_id["mornye_heavy_geopotential_shift"]["mechanic_effects"]["scheduled_healing_target_scope"]
        == TARGET_SCOPE
    )
    assert (
        by_id["mornye_liberation_critical_protocol"]["mechanic_effects"]["scheduled_healing_target_scope"]
        == TARGET_SCOPE
    )

    root_manifest = (ROOT / "direct_action_data_patch_manifest_v61.json").read_bytes()
    source_manifest = (ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json").read_bytes()
    assert root_manifest == source_manifest
    assert hashlib.sha256(root_manifest).hexdigest() == patcher.EXPECTED_MANIFEST_SHA256
    manifest = json.loads(root_manifest.decode("utf-8"))
    assert manifest["mornye_syntony_field_healing_patches"]["formula"]["target_scope"] == TARGET_SCOPE
    manifest_text = root_manifest.decode("utf-8")
    assert TARGET_SCOPE in manifest_text

    report = (ROOT / "reports" / "mornye_syntony_field_healing_scheduler_audit.md").read_text(encoding="utf-8")
    assert TARGET_SCOPE in report
    assert "generic 0.5-second swaps use the incoming destination as the host actor" in report.lower()

    print("scheduled_healing_host_actor_metadata_smoke_test ok")


if __name__ == "__main__":
    main()
