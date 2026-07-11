from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json"
ACTIONS_PATH = PROJECT_ROOT / "data" / "actions.json"
TRANSITIONS_PATH = PROJECT_ROOT / "data" / "transition_actions.json"
CHANGE_LOG_PATH = PROJECT_ROOT / "data" / "extracted" / "direct_action_data_v61_applied_changes.json"
EXPECTED_MANIFEST_SHA256 = "d3a75ab243469dabdce3b07e2adf0936511b6851a5d69f33f94087ff5054bf9a"

ACTION_VALUE_FIELDS = (
    "duration",
    "action_time",
    "combat_time_cost",
    "resonance_energy_gain",
    "concerto_energy_gain",
)
TRANSITION_VALUE_FIELDS = (
    "action_time",
    "combat_time_cost",
    "resonance_energy_gain",
    "concerto_energy_gain",
)


class AlignmentError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_records(records: list[dict[str, Any]], file_label: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for record in records:
        action_id = record.get("id")
        if not isinstance(action_id, str):
            raise AlignmentError(f"{file_label} contains a record without a string id")
        if action_id in index:
            duplicates.append(action_id)
        index[action_id] = record
    if duplicates:
        raise AlignmentError(f"{file_label} contains duplicate ids: {sorted(set(duplicates))}")
    return index


def patch_index(patches: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for patch in patches:
        action_id = patch.get(key)
        if not isinstance(action_id, str):
            raise AlignmentError(f"manifest patch missing string {key}: {patch!r}")
        if action_id in index:
            duplicates.append(action_id)
        index[action_id] = patch
    if duplicates:
        raise AlignmentError(f"manifest contains duplicate {key}s: {sorted(set(duplicates))}")
    return index


def clean_timing_overrides(overrides: dict[str, Any]) -> dict[str, dict[str, float]]:
    cleaned: dict[str, dict[str, float]] = {}
    for name, override in overrides.items():
        if not isinstance(override, dict):
            raise AlignmentError(f"timing override {name!r} is not an object")
        cleaned[name] = {}
        for field in ("action_time", "combat_time_cost"):
            if field not in override:
                raise AlignmentError(f"timing override {name!r} is missing {field}")
            cleaned[name][field] = float(override[field])
    return cleaned


def add_structural_hit_fields(hit: dict[str, Any], after: dict[str, Any], action_id: str) -> dict[str, Any]:
    mode = after.get("hit_time_mode")
    if mode is None:
        return hit
    if mode != "resolved_action_end":
        raise AlignmentError(f"{action_id} has unsupported after.hit_time_mode {mode!r}")
    hit["hit_time_mode"] = mode
    return hit


def source_evidence(patch: dict[str, Any]) -> dict[str, Any]:
    return {
        "confidence": patch.get("confidence"),
        "source_rows": patch.get("source_rows", []),
        "source_evidence": patch.get("source_evidence", {}),
    }


def record_change(
    changes: list[dict[str, Any]],
    *,
    target_file: str,
    action_id: str,
    field: str,
    before: Any,
    after: Any,
    patch: dict[str, Any],
) -> None:
    if before == after:
        return
    changes.append(
        {
            "target_file": target_file,
            "action_id": action_id,
            "field": field,
            "before": before,
            "after": after,
            "source_evidence": source_evidence(patch),
        }
    )


def set_field(
    record: dict[str, Any],
    field: str,
    value: Any,
    changes: list[dict[str, Any]],
    *,
    target_file: str,
    action_id: str,
    patch: dict[str, Any],
) -> None:
    before = copy.deepcopy(record.get(field))
    record[field] = value
    record_change(
        changes,
        target_file=target_file,
        action_id=action_id,
        field=field,
        before=before,
        after=copy.deepcopy(value),
        patch=patch,
    )


def apply_action_patch(record: dict[str, Any], patch: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    action_id = patch["action_id"]
    after = patch.get("after")
    if not isinstance(after, dict):
        raise AlignmentError(f"{action_id} missing manifest after object")

    for field in ACTION_VALUE_FIELDS:
        if field not in after:
            raise AlignmentError(f"{action_id} missing after.{field}")
        set_field(
            record,
            field,
            float(after[field]),
            changes,
            target_file="data/actions.json",
            action_id=action_id,
            patch=patch,
        )

    timing_overrides = clean_timing_overrides(after.get("timing_overrides", {}))
    if timing_overrides or record.get("timing_overrides"):
        set_field(
            record,
            "timing_overrides",
            timing_overrides,
            changes,
            target_file="data/actions.json",
            action_id=action_id,
            patch=patch,
        )

    damage_kind = patch.get("damage_kind")
    action_time = float(after["action_time"])
    tags = list(record.get("tags") or [])
    hit_name = f"{record.get('name', action_id)} hit"

    if damage_kind == "tune_break":
        if "tune_break_total" not in after:
            raise AlignmentError(f"{action_id} missing after.tune_break_total")
        total = float(after["tune_break_total"])
        hits = [
            add_structural_hit_fields({
                "time": action_time,
                "damage_category": "tune_break",
                "damage_multiplier": 0.0,
                "tune_break_multiplier": total,
                "tags": tags,
                "name": f"{record.get('name', action_id)} tune break",
            }, after, action_id)
        ] if total > 0.0 else []
        set_field(record, "damage_multiplier", 0.0, changes, target_file="data/actions.json", action_id=action_id, patch=patch)
        set_field(record, "tune_break_multiplier", total, changes, target_file="data/actions.json", action_id=action_id, patch=patch)
        set_field(record, "hits", hits, changes, target_file="data/actions.json", action_id=action_id, patch=patch)
        return

    if damage_kind != "direct":
        raise AlignmentError(f"{action_id} has unsupported damage_kind {damage_kind!r}")
    if "damage_total" not in after:
        raise AlignmentError(f"{action_id} missing after.damage_total")
    total = float(after["damage_total"])
    if total > 0.0:
        damage_category = record.get("damage_category", "normal")
        hits = [
            add_structural_hit_fields({
                "time": action_time,
                "damage_category": damage_category,
                "damage_multiplier": total,
                "tune_break_multiplier": 0.0,
                "tags": tags,
                "name": hit_name,
            }, after, action_id)
        ]
    else:
        hits = []
    set_field(record, "damage_multiplier", total, changes, target_file="data/actions.json", action_id=action_id, patch=patch)
    set_field(record, "tune_break_multiplier", 0.0, changes, target_file="data/actions.json", action_id=action_id, patch=patch)
    set_field(record, "hits", hits, changes, target_file="data/actions.json", action_id=action_id, patch=patch)


def apply_transition_patch(record: dict[str, Any], patch: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    action_id = patch["action_id"]
    after = patch.get("after")
    if not isinstance(after, dict):
        raise AlignmentError(f"{action_id} missing manifest after object")
    for field in TRANSITION_VALUE_FIELDS:
        if field not in after:
            raise AlignmentError(f"{action_id} missing after.{field}")
        set_field(
            record,
            field,
            float(after[field]),
            changes,
            target_file="data/transition_actions.json",
            action_id=action_id,
            patch=patch,
        )
    if "damage_total" not in after:
        raise AlignmentError(f"{action_id} missing after.damage_total")
    hits = [float(after["damage_total"])] if float(after["damage_total"]) > 0.0 else []
    set_field(record, "hits", hits, changes, target_file="data/transition_actions.json", action_id=action_id, patch=patch)


def apply_manifest_documents(
    manifest: dict[str, Any],
    actions: list[dict[str, Any]],
    transitions: list[dict[str, Any]],
    *,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not isinstance(actions, list) or not isinstance(transitions, list):
        raise AlignmentError("actions and transition action files must contain JSON arrays")

    action_ids_before = [record["id"] for record in actions]
    policy_ids_before = [record["id"] for record in actions if record.get("policy_selectable", True)]
    transition_ids_before = [record["id"] for record in transitions]

    action_records = index_records(actions, "data/actions.json")
    transition_records = index_records(transitions, "data/transition_actions.json")
    action_patches = patch_index(manifest.get("action_patches", []), "action_id")
    transition_patches = patch_index(manifest.get("transition_action_patches", []), "action_id")

    if len(action_patches) != 74:
        raise AlignmentError(f"expected 74 action patches, got {len(action_patches)}")
    if len(transition_patches) != 4:
        raise AlignmentError(f"expected 4 transition patches, got {len(transition_patches)}")

    missing_actions = sorted(set(action_patches) - set(action_records))
    missing_transitions = sorted(set(transition_patches) - set(transition_records))
    if missing_actions:
        raise AlignmentError(f"manifest action ids missing from data/actions.json: {missing_actions}")
    if missing_transitions:
        raise AlignmentError(f"manifest transition ids missing from data/transition_actions.json: {missing_transitions}")

    changes: list[dict[str, Any]] = []
    for patch in manifest["action_patches"]:
        apply_action_patch(action_records[patch["action_id"]], patch, changes)
    for patch in manifest["transition_action_patches"]:
        apply_transition_patch(transition_records[patch["action_id"]], patch, changes)

    action_ids_after = [record["id"] for record in actions]
    policy_ids_after = [record["id"] for record in actions if record.get("policy_selectable", True)]
    transition_ids_after = [record["id"] for record in transitions]
    if action_ids_after != action_ids_before:
        raise AlignmentError("data/actions.json action id order changed")
    if policy_ids_after != policy_ids_before:
        raise AlignmentError("data/actions.json policy-selectable action id order changed")
    if transition_ids_after != transition_ids_before:
        raise AlignmentError("data/transition_actions.json action id order changed")

    summary = {
        "manifest_sha256": manifest_hash,
        "action_patch_count": len(action_patches),
        "transition_patch_count": len(transition_patches),
        "field_level_change_count": len(changes),
        "action_id_order_unchanged": True,
        "policy_selectable_action_id_order_unchanged": True,
        "transition_action_id_order_unchanged": True,
    }
    return actions, transitions, changes, summary


def apply_manifest() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    manifest_hash = sha256(MANIFEST_PATH)
    if manifest_hash != EXPECTED_MANIFEST_SHA256:
        raise AlignmentError(
            f"manifest hash mismatch: expected {EXPECTED_MANIFEST_SHA256}, got {manifest_hash}"
        )

    manifest = load_json(MANIFEST_PATH)
    actions = load_json(ACTIONS_PATH)
    transitions = load_json(TRANSITIONS_PATH)
    return apply_manifest_documents(
        manifest,
        actions,
        transitions,
        manifest_hash=manifest_hash,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--fail-on-diff", action="store_true")
    args = parser.parse_args()

    try:
        actions, transitions, changes, summary = apply_manifest()
    except AlignmentError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.check:
        print(json.dumps({"mode": "check", **summary}, indent=2))
        if changes:
            print(f"{len(changes)} field-level differences found.")
            if args.fail_on_diff:
                return 1
        else:
            print("No field-level differences found.")
        return 0

    if changes:
        ACTIONS_PATH.write_text(dump_json(actions), encoding="utf-8")
        TRANSITIONS_PATH.write_text(dump_json(transitions), encoding="utf-8")
        CHANGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHANGE_LOG_PATH.write_text(
            dump_json(
                {
                    "summary": summary,
                    "changes": changes,
                }
            ),
            encoding="utf-8",
        )
    print(json.dumps({"mode": "apply", **summary}, indent=2))
    if not changes:
        print("No changes applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
