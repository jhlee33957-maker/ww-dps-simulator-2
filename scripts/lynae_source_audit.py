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
LYNAE_ACTION_ALIGNMENT = [
    ("lynae_basic_stage_1", "Basic Stage 1", [2577], [2408], "implemented_v2"),
    ("lynae_basic_stage_2", "Basic Stage 2", [2578, 2579, 2580], [2409, 2410, 2411], "implemented_v2"),
    ("lynae_basic_stage_3", "Basic Stage 3", [2581], [2412], "implemented_v2"),
    ("lynae_dodge_counter", "Dodge Counter", [2582], [2413], "implemented_v2"),
    ("lynae_mid_air_attack", "Mid-air Attack", [2583, 2584], [2414, 2415], "implemented_v2"),
    ("lynae_spark_collision_lv1", "Spark Collision Lv1", [2586, 2587], [2417, 2418], "implemented_v2"),
    ("lynae_spark_collision_lv2", "Spark Collision Lv2", [2588, 2589], [2419, 2420], "implemented_v2"),
    ("lynae_spark_collision_lv3", "Spark Collision Lv3", [2590, 2591], [2421, 2422], "implemented_v2"),
    ("lynae_kaleidoscopic_basic_stage_1", "KP Basic Stage 1", [2592, 2593, 2594], [2423], "implemented_v2"),
    ("lynae_kaleidoscopic_dodge_counter", "KP Dodge Counter", [2595], [2424], "implemented_v2"),
    ("lynae_kaleidoscopic_basic_stage_2", "KP Basic Stage 2", [2596, 2597], [2425, 2426], "implemented_v2"),
    ("lynae_kaleidoscopic_basic_stage_3", "KP Basic Stage 3", [2598, 2599, 2600], [2427, 2428, 2429], "implemented_v2"),
    ("lynae_kaleidoscopic_basic_stage_4", "KP Basic Stage 4", [2601, 2602, 2603, 2604, 2605], [2430, 2431, 2432, 2433], "implemented_v2"),
    ("lynae_kaleidoscopic_basic_stage_5", "KP Basic Stage 5", [2611, 2612, 2613, 2614], [2434, 2435, 2436], "implemented_v2"),
    ("lynae_kaleidoscopic_mid_air_attack", "KP Mid-air Attack", [2615, 2616], [2437, 2438], "implemented_v2"),
    ("lynae_kaleidoscopic_ground_heavy_hold", "KP Ground Heavy Hold", [2617, 2618, 2619, 2620, 2621, 2622, 2623], [2439, 2440, 2441, 2442, 2443, 2444, 2445], "implemented_v2_timing_simplified"),
    ("lynae_kaleidoscopic_graffiti_blast", "KP Graffiti Blast", [2624], [2446], "implemented_v2"),
    ("lynae_kaleidoscopic_mid_air_heavy", "KP Mid-air Heavy", [2633, 2634, 2635, 2636, 2637, 2638, 2639], [2447, 2448, 2449, 2450, 2451, 2452, 2453], "implemented_v2_timing_simplified"),
    ("lynae_resonance_skill_palette", "Lynae-Style Palettes", [2662, 2663, 2664, 2665, 2666], [2454, 2455, 2456, 2457], "implemented_v2"),
    ("lynae_resonance_skill_additive_color", "Additive Color", [2672, 2673, 2674], [2458, 2459], "implemented_v2"),
    ("lynae_iridescent_splash", "Iridescent Splash C0", [2675, 2676, 2677, 2678], [2460, 2461], "implemented_v2"),
    ("lynae_visual_impact", "Visual Impact C0", [2679, 2680, 2681, 2682], [2464, 2465], "implemented_v2_periodic_spray_metadata_only"),
    ("lynae_polychrome_leap_stage_1", "Polychrome Leap Stage 1 C0", [2641, 2642, 2643, 2644, 2645], [2468, 2469, 2470], "implemented_v2"),
    ("lynae_polychrome_leap_stage_2", "Polychrome Leap Stage 2 C0", [2647, 2648, 2649, 2650, 2651], [2474], "implemented_v2"),
    ("lynae_polychrome_leap_stage_3", "Polychrome Leap Stage 3 C0", [2653, 2654, 2660, 2661], [2476, 2477], "implemented_v2"),
    ("lynae_intro_time_to_show_some_colors", "Intro Skill", [2689, 2690, 2691], [2480, 2481], "implemented_v2"),
    ("lynae_resonance_liberation_prismatic_overblast", "Prismatic Overblast C0", [2692, 2693, 2694, 2695], [2482], "implemented_v2"),
    ("lynae_to_a_vivid_tomorrow", "To a Vivid Tomorrow", [2696, 2697, 2698], [2484, 2485], "implemented_v2"),
    ("lynae_outro_lets_hit_the_road", "Outro", [2699, 2700, 2701], [2486, 2487], "implemented_v2_tooltip_damage"),
    ("lynae_tune_break", "Tune Break", [2702, 2703, 2704], [2488], "metadata_only_zero_workbook_damage"),
    ("lynae_tune_response_spectral_analysis", "Spectral Analysis C0", [2735], [2489], "implemented_v2"),
]
LYNAE_ACTION_CALCULATIONS = {
    "lynae_kaleidoscopic_basic_stage_5": {
        "multiplier": 2.5181,
        "calculation_type": "additive_hits_with_repeated_tick",
        "additive_rows": [2434, 2436],
        "repeated_tick_rows": [{"damage_row": 2435, "action_row": 2613, "max_hits": 5}],
    },
    "lynae_iridescent_splash": {
        "multiplier": 3.0418,
        "calculation_type": "mutually_exclusive_mode_variants_same_multiplier",
        "mode_variant_rows": [2460, 2461],
    },
    "lynae_visual_impact": {
        "multiplier": 12.1672,
        "calculation_type": "mutually_exclusive_mode_variants_same_multiplier",
        "mode_variant_rows": [2464, 2465],
    },
    "lynae_polychrome_leap_stage_2": {
        "multiplier": 1.0140,
        "calculation_type": "repeated_tick_mode_variants_same_multiplier",
        "repeated_tick_rows": [{"damage_row": 2474, "action_rows": [2649, 2650], "max_hits": 6}],
        "mode_variant_action_rows": [2649, 2650],
    },
    "lynae_polychrome_leap_stage_3": {
        "multiplier": 0.6550,
        "calculation_type": "additive_hits_with_repeated_tick",
        "additive_rows": [2477],
        "repeated_tick_rows": [{"damage_row": 2476, "action_row": 2660, "max_hits": 4}],
    },
    "lynae_intro_time_to_show_some_colors": {
        "multiplier": 2.2480,
        "calculation_type": "repeated_tick_mutually_exclusive_mode_variants_same_multiplier",
        "mode_variant_rows": [2480, 2481],
        "repeated_tick_rows": [{"damage_rows": [2480, 2481], "action_row": 2689, "max_hits": 10}],
    },
    "lynae_resonance_liberation_prismatic_overblast": {
        "multiplier": 8.7480,
        "calculation_type": "repeated_tick",
        "repeated_tick_rows": [{"damage_row": 2482, "action_row": 2695, "max_hits": 10}],
    },
    "lynae_to_a_vivid_tomorrow": {
        "multiplier": 2.0106,
        "calculation_type": "additive_repeated_ticks",
        "repeated_tick_rows": [
            {"damage_row": 2484, "action_row": 2697, "max_hits": 12},
            {"damage_row": 2485, "action_row": 2698, "max_hits": 10},
        ],
    },
    "lynae_outro_lets_hit_the_road": {
        "multiplier": 1.0,
        "derived_tick_sum": 1.001,
        "calculation_type": "excel_tick_sum_and_tooltip_confirmed",
        "repeated_tick_rows": [
            {"damage_row": 2486, "rate_column": "Damage.RateLv_1", "action_row": 2700, "max_hits": 12},
            {"damage_row": 2487, "rate_column": "Damage.RateLv_1", "action_row": 2701, "max_hits": 10},
        ],
    },
    "lynae_tune_response_spectral_analysis": {
        "multiplier": 18.8075,
        "calculation_type": "tune_response_executable_source",
    },
}
LYNAE_CONSTELLATION_GATED_ACTIONS = {
    "lynae_iridescent_splash_c3": {
        "multiplier": 5.7795,
        "source_rows": ["dmg!2462", "dmg!2463"],
        "mode_variant_rows": [2462, 2463],
    },
    "lynae_visual_impact_c3": {
        "multiplier": 23.1177,
        "source_rows": ["dmg!2466", "dmg!2467"],
        "mode_variant_rows": [2466, 2467],
    },
    "lynae_polychrome_leap_stage_1_c1": {
        "multiplier": 2.2308,
        "source_rows": ["dmg!2471:2473"],
        "additive_rows": [2471, 2472, 2473],
    },
    "lynae_polychrome_leap_stage_2_c1": {
        "multiplier": 2.2308,
        "source_rows": ["dmg!2475"],
        "repeated_tick_rows": [{"damage_row": 2475, "action_row": 2649, "max_hits": 6}],
    },
    "lynae_polychrome_leap_stage_3_c1": {
        "multiplier": 1.4410,
        "source_rows": ["dmg!2478:2479"],
        "additive_rows": [2479],
        "repeated_tick_rows": [{"damage_row": 2478, "action_row": 2660, "max_hits": 4}],
    },
    "lynae_resonance_liberation_prismatic_overblast_c5": {
        "multiplier": 14.8710,
        "source_rows": ["dmg!2483"],
        "repeated_tick_rows": [{"damage_row": 2483, "action_row": 2695, "max_hits": 10}],
    },
    "lynae_tune_response_spectral_analysis_c2": {
        "multiplier": 31.9727,
        "source_rows": ["dmg!2490"],
    },
}
LYNAE_ADDITIVE_HIT_GROUPS = {
    "lynae_basic_stage_2": [2409, 2410, 2411],
    "lynae_mid_air_attack": [2414, 2415],
    "lynae_spark_collision_lv1": [2417, 2418],
    "lynae_spark_collision_lv2": [2419, 2420],
    "lynae_spark_collision_lv3": [2421, 2422],
    "lynae_kaleidoscopic_basic_stage_2": [2425, 2426],
    "lynae_kaleidoscopic_basic_stage_3": [2427, 2428, 2429],
    "lynae_kaleidoscopic_basic_stage_4": [2430, 2431, 2432, 2433],
    "lynae_kaleidoscopic_ground_heavy_hold": [2439, 2440, 2441, 2442, 2443, 2444, 2445],
    "lynae_kaleidoscopic_mid_air_heavy": [2447, 2448, 2449, 2450, 2451, 2452, 2453],
    "lynae_resonance_skill_palette": [2454, 2455, 2456, 2457],
    "lynae_resonance_skill_additive_color": [2458, 2459],
    "lynae_polychrome_leap_stage_1": [2468, 2469, 2470],
}
LYNAE_UNRESOLVED_ROWS = [
    {
        "topic": "continuous_lumiflow_movement_recovery",
        "source_rows": ["角色-女!2709"],
        "implementation_status": "user_tooltip_confirmed_timing_simplified",
        "reason": "Simulator is action-step based and has no continuous movement/skating state.",
    },
    {
        "topic": "spray_paint_periodic_ticks",
        "source_rows": ["角色-女!2683:2688"],
        "implementation_status": "metadata_only_window_recorded",
        "reason": "Visual Impact records the 5s window and immediate Flux; periodic 2s field scheduling is not added.",
    },
    {
        "topic": "constellation_variants",
        "source_rows": ["dmg!2462:2463", "dmg!2466:2467", "dmg!2471:2473", "dmg!2475", "dmg!2478:2479", "dmg!2483", "dmg!2490"],
        "implementation_status": "constellation_gated_disabled_by_default",
        "reason": "Non-S0 variants are retained as source-aligned records but not selected by default.",
    },
    {
        "topic": "skill_type_reference_region",
        "source_rows": ["角色技能类型!2553:2635"],
        "implementation_status": "workbook_reference_corrected",
        "reason": "Rows 772:784 are not the Lynae skill type region and are no longer used for Lynae.",
    },
]
LYNAE_IMPLEMENTED_SINGLE_TARGET_ROWS = [
    {
        "topic": "tune_strain_stack_limit_and_per_stack_damage",
        "source_rows": ["角色-女!2728"],
        "implementation_status": "implemented_single_target",
        "notes": (
            "Current single-target Endgame Matrix model increments Tune Strain Interfered stacks on Tune Break, "
            "caps at 1 stack for C0 and 2 stacks for C2+, lasts 30s, and applies only to Lynae damage. "
            "This is not a multi-target implementation claim."
        ),
    }
]


def lynae_unresolved_rows() -> list[dict[str, Any]]:
    return [
        item
        for item in LYNAE_UNRESOLVED_ROWS
        if not str(item.get("topic", "")).endswith("_implemented_single_target")
    ]


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
    rate_lv_1 = float(row[33] or 0.0)
    rate_lv_10 = float(row[42] or 0.0)
    return {
        "row": row_number,
        "character": row[0],
        "label": row[1],
        "source_label": row[2],
        "damage_element": row[8],
        "damage_type": row[9],
        "damage_related_property": row[32],
        "rate_lv_1": rate_lv_1,
        "rate_lv_10": rate_lv_10,
        "derived_multiplier": rate_lv_10 / 10000.0,
        "derived_multiplier_rate_lv_1": rate_lv_1 / 10000.0,
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
        passive_cache = cached_row_values(skill_type_sheet, 2553, 2635, max_col=24)
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

        passive_rows = row_values(passive_cache, 2553, 2635)
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
            "row_range": "2553:2635",
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
    action_map_path = EXTRACTED_DIR / "lynae_excel_action_map.json"
    unresolved_path = EXTRACTED_DIR / "lynae_excel_unresolved_rows.json"
    alignment_report_path = REPORTS_DIR / "lynae_excel_source_alignment.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    damage_by_row = {row["row"]: row for row in audit["damage_region"]["damage_rows"]}
    action_map = []
    for action_id, label, action_rows, damage_rows, implementation_status in LYNAE_ACTION_ALIGNMENT:
        multipliers = [float(damage_by_row[row]["derived_multiplier"]) for row in damage_rows if row in damage_by_row]
        calculation = dict(LYNAE_ACTION_CALCULATIONS.get(action_id, {}))
        multiplier = calculation.pop("multiplier", round(sum(multipliers), 10))
        calculation_type = calculation.pop("calculation_type", "additive_hits" if len(damage_rows) > 1 else "single_damage_row")
        action_map.append(
            {
                "action_id": action_id,
                "label": label,
                "workbook_sheet": "角色-女",
                "action_rows": action_rows,
                "damage_sheet": "dmg",
                "damage_rows": damage_rows,
                "multiplier": round(float(multiplier), 10),
                "damage_row_multipliers": {
                    str(row): damage_by_row[row]["derived_multiplier"] for row in damage_rows if row in damage_by_row
                },
                "damage_row_rate_lv_1_multipliers": {
                    str(row): damage_by_row[row]["derived_multiplier_rate_lv_1"]
                    for row in damage_rows
                    if row in damage_by_row and damage_by_row[row]["derived_multiplier_rate_lv_1"]
                },
                "calculation_type": calculation_type,
                **calculation,
                "timing_resource_evidence": [
                    row for row in audit["action_region"]["action_rows"] if row["row"] in set(action_rows)
                ],
                "source_status": "workbook_confirmed",
                "implementation_status": implementation_status,
            }
        )
    action_map_path.write_text(json.dumps(action_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    unresolved_path.write_text(json.dumps(lynae_unresolved_rows(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
            "- Tune Strain stack limit and per-stack damage are implemented for the current single-target Endgame Matrix model only; no multi-target behavior is claimed.",
            "- Complex Lumiflow movement recovery, skating movement speed, stamina, and air/ground branch exactness remain metadata-only/review-required in v1.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    alignment_lines = [
        "# Lynae Excel Source Alignment",
        "",
        f"Workbook: `{audit['workbook']}`",
        f"Source name: {audit['source_name']}",
        "",
        "## Source Regions",
        "- Damage coefficients: `dmg!2408:2490`",
        "- Action/timing/resources: `角色-女!2577:2738`",
        "- Skill type references: `角色技能类型!2553:2635`",
        "- Base stat reference: `prop!51`",
        "- Weapon reference only: `weapon!65`",
        "",
        "## Implemented Action Map",
    ]
    for item in action_map:
        alignment_lines.append(
            "- `{action_id}`: {label}; action rows {action_rows}; damage rows {damage_rows}; "
            "multiplier {multiplier}; calculation {calculation_type}; status {implementation_status}".format(**item)
        )
    alignment_lines.extend(["", "## Additive Hit Rows"])
    for action_id, rows in LYNAE_ADDITIVE_HIT_GROUPS.items():
        alignment_lines.append(f"- `{action_id}`: dmg!{', dmg!'.join(str(row) for row in rows)} are additive hits.")
    alignment_lines.extend(["", "## Repeated-Hit / Tick Rows"])
    for item in action_map:
        for rule in item.get("repeated_tick_rows", []):
            damage_rows = rule.get("damage_rows", [rule.get("damage_row")])
            damage_rows_text = ", ".join(f"dmg!{row}" for row in damage_rows if row is not None)
            action_rows_value = rule.get("action_rows", [rule.get("action_row")])
            action_rows_text = ", ".join(f"角色-女!{row}" for row in action_rows_value if row is not None)
            alignment_lines.append(
                f"- `{item['action_id']}`: {damage_rows_text} repeats max {rule['max_hits']} from {action_rows_text}."
            )
    alignment_lines.extend(["", "## Mutually Exclusive Mode Variants"])
    for item in action_map:
        rows = item.get("mode_variant_rows")
        if rows:
            alignment_lines.append(
                f"- `{item['action_id']}`: {', '.join(f'dmg!{row}' for row in rows)} are mode variants and are not additive."
            )
    alignment_lines.extend(["", "## Constellation-Gated Disabled By Default"])
    for action_id, item in LYNAE_CONSTELLATION_GATED_ACTIONS.items():
        alignment_lines.append(
            f"- `{action_id}`: multiplier {item['multiplier']}; rows {', '.join(item['source_rows'])}; disabled by default."
        )
    alignment_lines.extend(["", "## Implemented Single-Target Mechanics"])
    for item in LYNAE_IMPLEMENTED_SINGLE_TARGET_ROWS:
        alignment_lines.append(
            f"- {item['topic']}: {item['implementation_status']} ({', '.join(item['source_rows'])}) - {item['notes']}"
        )
    alignment_lines.extend(["", "## Unresolved / Metadata-Only Rows"])
    for item in lynae_unresolved_rows():
        alignment_lines.append(
            f"- {item['topic']}: {item['implementation_status']} ({', '.join(item['source_rows'])}) - {item['reason']}"
        )
    alignment_report_path.write_text("\n".join(alignment_lines) + "\n", encoding="utf-8")


def main() -> None:
    audit = build_audit()
    write_outputs(audit)
    print("lynae_source_audit ok: dmg!2489 multiplier", audit["spectral_analysis"]["derived_multiplier"])


if __name__ == "__main__":
    main()
