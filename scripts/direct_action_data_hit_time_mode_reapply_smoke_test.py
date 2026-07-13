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


AFFECTED_ACTION_IDS = (
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_2",
)
EXPECTED_MODE = "resolved_action_end"


def index(records: list[dict]) -> dict[str, dict]:
    return {record["id"]: record for record in records}


def hit_time_mode(record: dict) -> str | None:
    hits = record.get("hits") or []
    assert len(hits) == 1, f"{record['id']} should use one lumped hit"
    return hits[0].get("hit_time_mode")


def apply_to(actions: list[dict]) -> tuple[list[dict], list[dict], list[dict], dict]:
    manifest = load_json(MANIFEST_PATH)
    transitions = copy.deepcopy(load_json(TRANSITIONS_PATH))
    return apply_manifest_documents(
        manifest,
        actions,
        transitions,
        manifest_hash=sha256(MANIFEST_PATH),
    )


def main() -> None:
    actions = copy.deepcopy(load_json(ACTIONS_PATH))
    records = index(actions)

    for action_id in AFFECTED_ACTION_IDS:
        records[action_id]["hits"][0].pop("hit_time_mode", None)
        assert hit_time_mode(records[action_id]) is None

    patched_actions, _transitions, changes, summary = apply_to(actions)
    assert summary["field_level_change_count"] == len(changes)
    assert changes, "missing hit_time_mode fields should be detected"
    patched_records = index(patched_actions)
    for action_id in AFFECTED_ACTION_IDS:
        assert hit_time_mode(patched_records[action_id]) == EXPECTED_MODE

    _again_actions, _again_transitions, again_changes, again_summary = apply_to(patched_actions)
    assert again_summary["field_level_change_count"] == 0
    assert again_changes == []

    patched_records[AFFECTED_ACTION_IDS[0]]["hits"][0]["hit_time_mode"] = "static"
    _checked_actions, _checked_transitions, check_changes, check_summary = apply_to(patched_actions)
    assert check_summary["field_level_change_count"] > 0
    assert check_changes, "incorrect hit_time_mode should be detected"

    restored_records = index(_checked_actions)
    assert hit_time_mode(restored_records[AFFECTED_ACTION_IDS[0]]) == EXPECTED_MODE


if __name__ == "__main__":
    main()
