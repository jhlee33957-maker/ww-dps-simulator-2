from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "data" / "extracted" / "off_tune_value_mapping_audit.json"
REPORT_PATH = ROOT / "reports" / "off_tune_value_mapping_audit.md"
ACTIONS_PATH = ROOT / "data" / "actions.json"

ROLE_FEMALE_SHEET = "\u89d2\u8272-\u5973"
SKILL_TYPE_SHEET = "\u89d2\u8272\u6280\u80fd\u7c7b\u578b"
DAMAGE_1_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4126"
DAMAGE_2_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4127"

assert [ord(c) for c in ROLE_FEMALE_SHEET] == [0x89D2, 0x8272, 0x002D, 0x5973]
assert [ord(c) for c in SKILL_TYPE_SHEET] == [0x89D2, 0x8272, 0x6280, 0x80FD, 0x7C7B, 0x578B]

GENERATED_SYNTONY_NOTES = {
    "mornye_syntony_field_damage": (
        "Mornye Syntony Field Damage 1 deals damage but has a source-confirmed "
        "Off-Tune contribution of 0. Its repeated executions are supplied by the "
        "scheduled-effect engine."
    ),
    "mornye_syntony_field_target_damage": (
        "Mornye Syntony Field Damage 2 is the non-QTE target-position deployment "
        "event and owns the source-confirmed Off-Tune contribution of 66.4."
    ),
}
LEGACY_GENERATED_SYNTONY_NOTES = {
    (
        "The payload deals damage but its source-confirmed Off-Tune contribution is zero. "
        "Its repeated executions are supplied by the scheduled-effect engine."
    ),
    (
        "The payload is the non-QTE target-position deployment event and carries the "
        "source-confirmed Off-Tune contribution."
    ),
}
GENERATED_SYNTONY_NOTE_ORDER = [
    "mornye_syntony_field_damage",
    "mornye_syntony_field_target_damage",
]

SYNTONY_MAPPING_ROWS = [
    {
        "action_id": "mornye_syntony_field_damage",
        "source_ref": DAMAGE_1_ACTION_REF,
        "source_rows": [4126],
        "source_status": "workbook_confirmed_zero_for_damage_1",
        "note": GENERATED_SYNTONY_NOTES["mornye_syntony_field_damage"],
    },
    {
        "action_id": "mornye_syntony_field_target_damage",
        "source_ref": DAMAGE_2_ACTION_REF,
        "source_rows": [4127],
        "source_status": "workbook_confirmed",
        "note": GENERATED_SYNTONY_NOTES["mornye_syntony_field_target_damage"],
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def action_index() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in load_json(ACTIONS_PATH)}


def syntony_mapping(row: dict[str, Any], actions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    action = actions[row["action_id"]]
    return {
        "action_id": row["action_id"],
        "off_tune_value": float(action["off_tune_value"]),
        "source_status": row["source_status"],
        "source_ref": row["source_ref"],
        "source_rows": row["source_rows"],
        "sheet": ROLE_FEMALE_SHEET,
        "column": "S",
        "policy_selectable": bool(action.get("policy_selectable", True)),
        "damaging_action": True,
        "note": row["note"],
    }


def update_audit(audit: dict[str, Any], actions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    old_mappings = audit["mappings"]
    insertion_index = next(
        index for index, row in enumerate(old_mappings) if row["action_id"] == "mornye_syntony_field_damage"
    )
    mappings = [
        row
        for row in old_mappings
        if row["action_id"] not in {"mornye_syntony_field_damage", "mornye_syntony_field_target_damage"}
    ]
    for offset, row in enumerate(SYNTONY_MAPPING_ROWS):
        mappings.insert(insertion_index + offset, syntony_mapping(row, actions))
    audit["mappings"] = mappings

    checked = [
        action_id
        for action_id in audit["damaging_actions_checked"]
        if action_id != "mornye_syntony_field_target_damage"
    ]
    damage_1_index = checked.index("mornye_syntony_field_damage")
    checked.insert(damage_1_index + 1, "mornye_syntony_field_target_damage")
    audit["damaging_actions_checked"] = checked
    audit["unresolved_damaging_action_ids"] = [
        action_id
        for action_id in audit["unresolved_damaging_action_ids"]
        if action_id not in {"mornye_syntony_field_damage", "mornye_syntony_field_target_damage"}
    ]
    generator_owned_notes = set(GENERATED_SYNTONY_NOTES.values()) | LEGACY_GENERATED_SYNTONY_NOTES
    audit["notes"] = [note for note in audit.get("notes", []) if note not in generator_owned_notes]
    audit["notes"].extend(GENERATED_SYNTONY_NOTES[action_id] for action_id in GENERATED_SYNTONY_NOTE_ORDER)
    return audit


def generate_report(audit: dict[str, Any]) -> str:
    unresolved = audit["unresolved_damaging_action_ids"] or ["none"]
    lines = [
        "# Off-Tune Value Mapping Audit",
        "",
        f"- Source: user-provided workbook, `{ROLE_FEMALE_SHEET}` column S.",
        f"- Boss Tune Break cooldown: {audit['boss_tune_break_cooldown_seconds']}s from `{audit['boss_tune_break_cooldown_source_ref']}` for COST4/red-name targets.",
        "- Cooldown rule: Off-Tune accumulation is blocked entirely while Tune Break cooldown is active.",
        "- Mapping rule: sum column S across separate workbook rows mapped to one simulator action; apply repeat-aware expansion only when a workbook frame-row repeat note is explicitly confirmed for the action.",
        f"- Damaging actions checked: {len(audit['damaging_actions_checked'])}.",
        f"- Mapped action count: {len(audit['mappings'])}.",
        f"- Unresolved damaging action ids: {', '.join(unresolved)}.",
        f"- Internal alias action ids: {audit['internal_alias_action_ids']}.",
        "",
        "## Completeness Guard Patch",
        "",
        f"- Actions with missing Off-Tune metadata before patch: {audit['actions_with_missing_off_tune_metadata_before_patch']}.",
        "- Actions with missing Off-Tune metadata after patch: none.",
        f"- Completeness status: `{audit['off_tune_mapping_completeness_status']}`.",
        "",
        "| Action | Final Status | Off-Tune | Source Status | Source Ref | Alias Of |",
        "|---|---|---:|---|---|---|",
    ]
    for row in audit["actions_fixed_this_patch"]:
        lines.append(
            "| `{action_id}` | `{final_status}` | {off_tune_value} | `{source_status}` | `{source_ref}` | {alias_of} |".format(
                action_id=row["action_id"],
                final_status=row["final_status"],
                off_tune_value=row["off_tune_value"],
                source_status=row["source_status"],
                source_ref=row["source_ref"],
                alias_of=f"`{row['alias_of']}`" if row.get("alias_of") else "",
            )
        )
    lines.extend(
        [
            "",
            "## Key Corrections",
            "",
            f"- `mornye_heavy_geopotential_shift`: 29.6 from `{ROLE_FEMALE_SHEET}!S4117`.",
            f"- `mornye_heavy_inversion`: 104.0 from `{ROLE_FEMALE_SHEET}!S4136`.",
            f"- `aemeath_mech_basic_stage_3`: 62.54 repeat-aware Off-Tune from `{ROLE_FEMALE_SHEET}!S2889:S2892`, with A3-2 repeated by `{ROLE_FEMALE_SHEET}!D2890`.",
            f"- `aemeath_seraphic_duet_encore`: 128.0 from `{ROLE_FEMALE_SHEET}!S2925:S2929`.",
            "",
            "## Notes",
            "",
            *[f"- {note}" for note in audit.get("notes", [])],
            "",
            "## Mappings",
            "",
            "| Action | Off-Tune | Source Status | Source Ref | Alias Of |",
            "|---|---:|---|---|---|",
        ]
    )
    for row in audit["mappings"]:
        alias = row.get("alias_of")
        lines.append(
            "| `{action_id}` | {off_tune_value} | `{source_status}` | `{source_ref}` | {alias_of} |".format(
                action_id=row["action_id"],
                off_tune_value=row["off_tune_value"],
                source_status=row["source_status"],
                source_ref=row["source_ref"],
                alias_of=f"`{alias}`" if alias else "",
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    actions = action_index()
    audit = update_audit(load_json(AUDIT_PATH), actions)
    dump_json(AUDIT_PATH, audit)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(generate_report(audit))
    print("off_tune_value_mapping_audit regenerated")


if __name__ == "__main__":
    main()
