from __future__ import annotations

import copy
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.apply_direct_action_data_v61 import (
    ACTIONS_PATH,
    MANIFEST_PATH,
    TRANSITIONS_PATH,
    apply_manifest_documents,
    load_json,
    sha256,
)


UNRESOLVED_ID = "lynae_echo_hyvatia"


def index(records: list[dict]) -> dict[str, dict]:
    return {record["id"]: record for record in records}


def reset_lynae_off_tune(actions: list[dict], transitions: list[dict], manifest: dict) -> None:
    action_records = index(actions)
    transition_records = index(transitions)
    for patch in manifest["lynae_off_tune_action_patches"]:
        record = action_records[patch["action_id"]]
        record["off_tune_value"] = 0.0
        record["off_tune_value_source_status"] = "unresolved_missing_excel_mapping"
        record["off_tune_value_source_ref"] = None
        record.pop("off_tune_value_alias_of", None)
        record.pop("off_tune_value_alias_note", None)
    for patch in manifest["lynae_off_tune_transition_patches"]:
        record = transition_records[patch["action_id"]]
        record["off_tune_value"] = 0.0
        record["off_tune_value_source_status"] = "unresolved_missing_excel_mapping"
        record["off_tune_value_source_ref"] = None


def assert_lynae_off_tune(actions: list[dict], transitions: list[dict], manifest: dict) -> None:
    action_records = index(actions)
    transition_records = index(transitions)
    for patch in manifest["lynae_off_tune_action_patches"]:
        record = action_records[patch["action_id"]]
        assert record["off_tune_value"] == patch["off_tune_value"]
        assert record["off_tune_value_source_status"] == patch["off_tune_value_source_status"]
        assert record.get("off_tune_value_source_ref") == patch.get("off_tune_value_source_ref")
        if patch.get("off_tune_value_alias_of") is None:
            assert record.get("off_tune_value_alias_of") is None
            assert record.get("off_tune_value_alias_note") is None
        else:
            assert record.get("off_tune_value_alias_of") == patch["off_tune_value_alias_of"]
            assert record.get("off_tune_value_alias_note") == patch["off_tune_value_alias_note"]
    assert action_records[UNRESOLVED_ID]["off_tune_value"] == 0.0
    assert action_records[UNRESOLVED_ID]["off_tune_value_source_status"] == "unresolved_echo_off_tune"

    for patch in manifest["lynae_off_tune_transition_patches"]:
        record = transition_records[patch["action_id"]]
        assert record["off_tune_value"] == patch["off_tune_value"]
        assert record["off_tune_value_source_status"] == patch["off_tune_value_source_status"]
        assert record.get("off_tune_value_source_ref") == patch.get("off_tune_value_source_ref")


def main() -> None:
    manifest = load_json(MANIFEST_PATH)
    manifest_hash = sha256(MANIFEST_PATH)
    actions = copy.deepcopy(load_json(ACTIONS_PATH))
    transitions = copy.deepcopy(load_json(TRANSITIONS_PATH))
    reset_lynae_off_tune(actions, transitions, manifest)

    patched_actions, patched_transitions, changes, summary = apply_manifest_documents(
        manifest,
        actions,
        transitions,
        manifest_hash=manifest_hash,
    )
    assert summary["lynae_off_tune_action_patch_count"] == 43
    assert summary["lynae_off_tune_transition_patch_count"] == 1
    assert summary["field_level_change_count"] == len(changes)
    assert changes, "reset Lynae Off-Tune fields should be restored by the manifest"
    assert_lynae_off_tune(patched_actions, patched_transitions, manifest)

    _again_actions, _again_transitions, again_changes, again_summary = apply_manifest_documents(
        manifest,
        patched_actions,
        patched_transitions,
        manifest_hash=manifest_hash,
    )
    assert again_summary["field_level_change_count"] == 0
    assert again_changes == []

    print("lynae_off_tune_manifest_reapply_smoke_test ok")


if __name__ == "__main__":
    main()
