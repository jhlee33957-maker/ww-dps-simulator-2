from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
EXTRACTED_DIR = DATA_DIR / "extracted"
REPORTS_DIR = ROOT / "reports"

WORKBOOK_ALIASES = {
    "action_sheet": "角色-女",
    "skill_type_sheet": "角色技能类型",
    "appendix2_sheet": "附页2",
}
PREFERRED_SHEETS = {"角色-女", "dmg", "prop", "weapon"}


def workbook_sheet_names(workbook_path: Path) -> set[str]:
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    try:
        return set(workbook.sheetnames)
    finally:
        workbook.close()


def select_source_workbook() -> Path:
    workbook_paths = sorted(SOURCE_DIR.glob("*.xlsx"))
    if not workbook_paths:
        raise FileNotFoundError(f"No .xlsx source workbook found in {SOURCE_DIR}")
    if len(workbook_paths) == 1:
        return workbook_paths[0]

    matching_paths = []
    for workbook_path in workbook_paths:
        if PREFERRED_SHEETS.issubset(workbook_sheet_names(workbook_path)):
            matching_paths.append(workbook_path)

    if matching_paths:
        return matching_paths[0]

    expected = ", ".join(sorted(PREFERRED_SHEETS))
    found = ", ".join(path.name for path in workbook_paths)
    raise FileNotFoundError(f"No source workbook with required sheets ({expected}) found. Candidates: {found}")


def cached_row_values(sheet: Any, start: int, end: int, max_col: int = 80) -> dict[int, list[Any]]:
    result = {}
    for row_number, row in enumerate(
        sheet.iter_rows(
            min_row=start,
            max_row=end,
            min_col=1,
            max_col=max_col,
            values_only=True,
        ),
        start=start,
    ):
        result[row_number] = list(row)
    return result


def row_values(row_cache: dict[int, list[Any]], start: int, end: int) -> list[dict[str, Any]]:
    rows = []
    for row_number in range(start, end + 1):
        values = row_cache.get(row_number, [])
        if any(value is not None for value in values):
            rows.append(
                {
                    "row": row_number,
                    "values": values,
                    "text": " | ".join("" if value is None else str(value) for value in values),
                }
            )
    return rows


def damage_row_from_cache(row_cache: dict[int, list[Any]], row_number: int) -> dict[str, Any]:
    row = row_cache[row_number]
    rate_lv_10 = float(row[42] or 0.0)
    return {
        "row": row_number,
        "character": row[0],
        "label": row[1],
        "source_label": row[2],
        "damage_element": row[8],
        "damage_type": row[9],
        "damage_related_property": row[32],
        "rate_lv_10": rate_lv_10,
        "derived_multiplier": rate_lv_10 / 10000.0,
        "source_status": "workbook_confirmed",
        "values": list(row),
    }


def classify_action_row(row: dict[str, Any]) -> str:
    text = row["text"]
    if any(token in text for token in ["流光", "溢彩", "真彩", "轮滑", "光色"]):
        return "workbook_confirmed"
    if any(token in text for token in ["共鸣模式", "震谐响应", "光谱分析"]):
        return "metadata_only"
    return "review_required"


def build_audit() -> dict[str, Any]:
    workbook_path = select_source_workbook()
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    try:
        action_sheet = workbook["角色-女"]
        dmg_sheet = workbook["dmg"]
        skill_type_sheet = workbook["角色技能类型"]
        weapon_sheet = workbook["weapon"]
        prop_sheet = workbook["prop"]

        action_cache = cached_row_values(action_sheet, 2577, 2738, max_col=24)
        dmg_cache = cached_row_values(dmg_sheet, 2408, 2490, max_col=80)
        passive_cache = cached_row_values(skill_type_sheet, 772, 784, max_col=24)
        weapon_cache = cached_row_values(weapon_sheet, 65, 65, max_col=24)
        prop_cache = cached_row_values(prop_sheet, 51, 51, max_col=24)

        action_rows = row_values(action_cache, 2577, 2738)
        for row in action_rows:
            row["classification"] = classify_action_row(row)

        dmg_rows = [damage_row_from_cache(dmg_cache, row_number) for row_number in range(2408, 2491)]
        dmg_rows = [row for row in dmg_rows if row["character"] == "琳奈"]
        spectral = next(row for row in dmg_rows if row["row"] == 2489)
        c2 = next(row for row in dmg_rows if row["row"] == 2490)
        c2["source_status"] = "disabled_by_default_constellation"
        c2["implementation_status"] = "constellation_gated_disabled_by_default"

        passive_rows = row_values(passive_cache, 772, 784)
        weapon_row = row_values(weapon_cache, 65, 65)
        prop_row = row_values(prop_cache, 51, 51)
    finally:
        workbook.close()

    findings = [
        {
            "id": "lynae_spectral_analysis",
            "label": "震谐响应",
            "source_ref": "dmg!2489",
            "multiplier": spectral["derived_multiplier"],
            "classification": "workbook_confirmed",
        },
        {
            "id": "lynae_spectral_analysis_c2",
            "label": "C2震谐响应",
            "source_ref": "dmg!2490",
            "multiplier": c2["derived_multiplier"],
            "classification": "disabled_by_default_constellation",
        },
        {
            "id": "static_mist",
            "label": "Static Mist",
            "source_ref": "user supplied weapon tooltip; weapon!65 reviewed for Lynae weapon candidate",
            "classification": "user_supplied_tooltip",
        },
        {
            "id": "lynae_user_real_01",
            "label": "User real profile stats",
            "source_ref": "user supplied stat panel",
            "classification": "user_profile",
        },
        {
            "id": "lynae_complex_movement_states",
            "label": "Lumiflow / skating / hold movement branches",
            "source_ref": "角色-女!2577:2738",
            "classification": "metadata_only",
        },
    ]

    return {
        "workbook": str(workbook_path.relative_to(ROOT)),
        "sheet_aliases": WORKBOOK_ALIASES,
        "source_name": "琳奈",
        "internal_id": "lynae",
        "action_region": {
            "sheet": "角色-女",
            "rows": "2577:2738",
            "rows_found": len(action_rows),
            "action_rows": action_rows,
        },
        "damage_region": {
            "sheet": "dmg",
            "rows": "2408:2490",
            "rows_found": len(dmg_rows),
            "damage_rows": dmg_rows,
        },
        "spectral_analysis": spectral,
        "spectral_analysis_c2": c2,
        "passive_buff_candidates": {
            "sheet": "角色技能类型",
            "rows": "772:784",
            "rows_found": len(passive_rows),
            "classification": "review_required",
            "rows": passive_rows,
        },
        "weapon_reference": {
            "sheet": "weapon",
            "row": 65,
            "classification": "metadata_only",
            "rows": weapon_row,
        },
        "base_stat_reference": {
            "sheet": "prop",
            "row": 51,
            "classification": "metadata_only",
            "rows": prop_row,
        },
        "findings": findings,
    }


def write_outputs(audit: dict[str, Any]) -> None:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = EXTRACTED_DIR / "lynae_source_audit.json"
    report_path = REPORTS_DIR / "lynae_source_audit.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Lynae Source Audit",
        "",
        f"Workbook: `{audit['workbook']}`",
        f"Source name: {audit['source_name']}",
        "",
        "## Key Findings",
    ]
    for finding in audit["findings"]:
        lines.append(
            f"- `{finding['id']}`: {finding['label']} ({finding['classification']}), source {finding['source_ref']}"
        )
    lines.extend(
        [
            "",
            "## Spectral Analysis",
            f"- dmg!2489 multiplier: {audit['spectral_analysis']['derived_multiplier']}",
            f"- dmg!2490 C2 multiplier: {audit['spectral_analysis_c2']['derived_multiplier']} (disabled by default)",
            "",
            "## Scope Notes",
            "- Static Mist, Pact of Neonlight Leap, Hyvatia, Liberation, and Outro buff values are user-supplied tooltip sources.",
            "- Complex Lumiflow movement recovery, skating movement speed, stamina, and air/ground branch exactness remain metadata-only/review-required in v1.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    audit = build_audit()
    write_outputs(audit)
    print("lynae_source_audit ok: dmg!2489 multiplier", audit["spectral_analysis"]["derived_multiplier"])


if __name__ == "__main__":
    main()
