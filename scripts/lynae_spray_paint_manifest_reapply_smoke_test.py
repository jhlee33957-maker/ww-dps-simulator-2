from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import scripts.apply_direct_action_data_v61 as patcher
from lynae_spray_paint_test_helpers import C1_OUT_OF_SCOPE_REFS, TUNE_RUPTURE_REF, TUNE_STRAIN_REF


PAYLOAD_ID = "lynae_spray_paint_flux_application"
CORRUPT_REF = "unresolved_spray_paint_source_ref"


def index(records: list[dict]) -> dict[str, dict]:
    return {record["id"]: record for record in records}


def reset_spray_paint(actions: list[dict]) -> None:
    action_records = index(actions)
    original_schedule = copy.deepcopy(
        action_records["lynae_visual_impact"]["mechanic_effects"]["spray_paint_status_schedule"]
    )
    actions[:] = [record for record in actions if record["id"] != PAYLOAD_ID]
    visual = index(actions)["lynae_visual_impact"]
    mechanic_effects = dict(visual.get("mechanic_effects") or {})
    original_schedule["mode_mapping"]["tune_strain"]["source_row"] = CORRUPT_REF
    original_schedule["mode_mapping"]["tune_rupture"]["source_row"] = CORRUPT_REF
    original_schedule["c1_rows_excluded"] = [CORRUPT_REF]
    mechanic_effects["spray_paint_status_schedule"] = original_schedule
    visual["mechanic_effects"] = mechanic_effects


def assert_spray_paint(actions: list[dict], manifest: dict) -> None:
    action_records = index(actions)
    section = manifest["lynae_spray_paint_status_patches"]
    payload_patch = section["payloads"][0]
    metadata_patch = section["action_metadata_records"][0]
    assert action_records[PAYLOAD_ID] == payload_patch["record"]
    visual = action_records["lynae_visual_impact"]
    assert visual["mechanic_effects"] == metadata_patch["fields"]["mechanic_effects"]
    schedule = visual["mechanic_effects"]["spray_paint_status_schedule"]
    assert schedule["payload_event_type"] == "status_application"
    assert schedule["relative_application_frames"] == [1, 121, 241]
    assert schedule["remove_on_max_trigger_count"] is False
    assert schedule["mode_mapping"]["tune_strain"]["source_row"] == TUNE_STRAIN_REF
    assert schedule["mode_mapping"]["tune_rupture"]["source_row"] == TUNE_RUPTURE_REF
    assert schedule["c1_rows_excluded"] == C1_OUT_OF_SCOPE_REFS


def main() -> None:
    manifest = patcher.load_json(patcher.MANIFEST_PATH)
    actions = copy.deepcopy(patcher.load_json(patcher.ACTIONS_PATH))
    transitions = copy.deepcopy(patcher.load_json(patcher.TRANSITIONS_PATH))
    policy_ids_before = [record["id"] for record in actions if record.get("policy_selectable", True)]
    reset_spray_paint(actions)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        temp_actions = tmp / "actions.json"
        temp_transitions = tmp / "transition_actions.json"
        temp_manifest = tmp / "direct_action_data_patch_manifest_v61.json"
        temp_change_log = tmp / "changes.json"
        temp_actions.write_text(json.dumps(actions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp_transitions.write_text(json.dumps(transitions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp_manifest.write_bytes(patcher.MANIFEST_PATH.read_bytes())

        old_paths = (
            patcher.ACTIONS_PATH,
            patcher.TRANSITIONS_PATH,
            patcher.MANIFEST_PATH,
            patcher.CHANGE_LOG_PATH,
        )
        old_argv = list(sys.argv)
        try:
            patcher.ACTIONS_PATH = temp_actions
            patcher.TRANSITIONS_PATH = temp_transitions
            patcher.MANIFEST_PATH = temp_manifest
            patcher.CHANGE_LOG_PATH = temp_change_log
            sys.argv = ["apply_direct_action_data_v61.py", "--apply"]
            assert patcher.main() == 0

            patched_actions = patcher.load_json(temp_actions)
            patched_transitions = patcher.load_json(temp_transitions)
            assert [record["id"] for record in patched_actions if record.get("policy_selectable", True)] == policy_ids_before
            assert_spray_paint(patched_actions, manifest)

            again_actions, again_transitions, again_changes, again_summary = patcher.apply_manifest_documents(
                manifest,
                patched_actions,
                patched_transitions,
                manifest_hash=patcher.sha256(temp_manifest),
            )
            assert again_actions == patched_actions
            assert again_transitions == patched_transitions
            assert again_summary["field_level_change_count"] == 0
            assert again_changes == []
        finally:
            (
                patcher.ACTIONS_PATH,
                patcher.TRANSITIONS_PATH,
                patcher.MANIFEST_PATH,
                patcher.CHANGE_LOG_PATH,
            ) = old_paths
            sys.argv = old_argv

    print("lynae_spray_paint_manifest_reapply_smoke_test ok")


if __name__ == "__main__":
    main()
