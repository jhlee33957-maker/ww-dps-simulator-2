from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FEMALE = "".join(map(chr, (0x89D2, 0x8272, 0x2D, 0x5973)))
SKILL_TYPES = "".join(map(chr, (0x89D2, 0x8272, 0x6280, 0x80FD, 0x7C7B, 0x578B)))
DAMAGE_CALC = "".join(map(chr, (0x4F24, 0x5BB3, 0x8BA1, 0x7B97)))
LYNAE_BWIKI_URL = "https://wiki.biligame.com/wutheringwaves/%E5%85%B1%E9%B8%A3%E8%80%85/%E7%90%B3%E5%A5%88"
KILL_TARGET = "".join(map(chr, (0x653B, 0x51FB, 0x51FB, 0x6740, 0x76EE, 0x6807)))
DURATION_REFRESH = "".join(map(chr, (0x6301, 0x7EED, 0x31, 0x79D2, 0xFF0C, 0x91CD, 0x590D, 0x547D, 0x4E2D, 0x5237, 0x65B0)))
DEATH_SETTLEMENT = "".join(map(chr, (0x6B7B, 0x4EA1, 0x65F6, 0xFF0C, 0x7ED3, 0x7B97)))
TUNE_RESPONSE = "".join(map(chr, (0x9707, 0x8C10, 0x54CD, 0x5E94)))
FUSION_APPLICATION = "".join(map(chr, (0x8D4B, 0x4E88, 0x76EE, 0x6807, 0x805A, 0x7206, 0x6548, 0x5E94)))
TUNE = "".join(map(chr, (0x9707, 0x8C10)))
FUSION = "".join(map(chr, (0x805A, 0x7206)))
FUSION_MODE = "".join(map(chr, (0x805A, 0x7206, 0x6A21, 0x6001)))
FUSION_EFFECT_WHEN = "".join(map(chr, (0x805A, 0x7206, 0x6548, 0x5E94, 0x65F6)))
SETTLEMENT = "".join(map(chr, (0x7ED3, 0x7B97)))
RADIANT_FULL = "".join(map(chr, (0x56DE, 0x6EE1)))


def workbook(character: str, sequence: int, refs: tuple[str, ...], tokens: tuple[str, ...], status: str = "implemented") -> dict:
    return {"character_id": character, "sequence": sequence, "support_status": status, "source_type": "workbook_exact", "refs": refs, "tokens": tokens}


CONTRACT = {
    "aemeath_s1_heavy_crit_damage": workbook("aemeath", 1, ("base!FE73", "base!FN73"), ("300%",)),
    "aemeath_s1_precombat_radiance": workbook("aemeath", 1, ("base!FE73", "base!FN73"), ("4",)),
    "aemeath_s1_charged_ii_sync": workbook("aemeath", 1, ("base!FE73", "base!FN73"), ("100",)),
    "aemeath_s1_kill_trajectory_transfer_unsupported": workbook("aemeath", 1, ("base!FE73", "base!FN73"), (KILL_TARGET, "10"), "unsupported_scope"),
    "aemeath_s2_direct_enhanced_skill_coefficient": workbook("aemeath", 2, ("base!FF73", "base!FO73"), ("100%",)),
    "aemeath_s2_tune_packet_normal": workbook("aemeath", 2, (f"{FEMALE}!C2786:D2787", f"{FEMALE}!C2931:D2932", f"{SKILL_TYPES}!A2724:I2725", "dmg!B2578:B2579"), ("4F", "5")),
    "aemeath_s2_tune_packet_enhanced": workbook("aemeath", 2, (f"{FEMALE}!C2786:D2787", f"{FEMALE}!C2931:D2932", f"{SKILL_TYPES}!A2779:I2780", "dmg!B2628:B2629"), ("2F", "10")),
    "aemeath_s2_tune_per_hit_stack": workbook("aemeath", 2, ("base!FF73", "base!FO73"), ("20%",)),
    "aemeath_s2_tune_stack_duration_refresh": workbook("aemeath", 2, ("base!FF73", "base!FO73"), (DURATION_REFRESH,)),
    "aemeath_s2_tune_trajectory_removed_bonus": workbook("aemeath", 2, (f"{FEMALE}!D2844",), ("4%",)),
    "aemeath_s2_fusion_base_enhancement_formula": workbook("aemeath", 2, (f"{FEMALE}!C2788:D2788", f"{FEMALE}!C2933:D2933", "dmg!B2589", "dmg!DB2589:DC2589", f"{DAMAGE_CALC}!T299:V308"), (SETTLEMENT, FUSION)),
    "aemeath_s2_fusion_c2_enhancement_formula": workbook("aemeath", 2, ("base!FF73", "base!FO73"), ("400%", "15%")),
    "aemeath_s2_kill_settlement_unsupported": workbook("aemeath", 2, (f"{FEMALE}!D2844",), (DEATH_SETTLEMENT,), "unsupported_scope"),
    "aemeath_s3_finale_coefficient": workbook("aemeath", 3, ("base!FG73", "base!FP73"), ("100%",)),
    "aemeath_s3_overdrive_coefficient": workbook("aemeath", 3, ("base!FG73", "base!FP73"), ("40%",)),
    "aemeath_s3_enhanced_heavy_mode_application": workbook("aemeath", 3, ("base!FG73", "base!FP73"), ("12",)),
    "aemeath_s3_tune_contributor_bonus": workbook("aemeath", 3, ("base!FL73", "base!FU73"), ("20%", "3")),
    "aemeath_s3_fusion_contributor_bonus": workbook("aemeath", 3, ("base!FL73", "base!FU73"), ("30%", "2")),
    "aemeath_s4_party_all_attribute_bonus": workbook("aemeath", 4, ("base!FH73", "base!FQ73"), ("30", "20%")),
    "aemeath_s5_kill_radiant_overflow_unsupported": workbook("aemeath", 5, ("base!FI73", "base!FR73"), (RADIANT_FULL,), "unsupported_scope"),
    "aemeath_s5_fatal_state_shield_revive_unsupported": workbook("aemeath", 5, ("base!FI73", "base!FR73"), ("600",), "unsupported_scope"),
    "aemeath_s6_liberation_target_deepen": workbook("aemeath", 6, ("base!FJ73", "base!FS73"), ("40%",)),
    "aemeath_s6_trajectory_cap": workbook("aemeath", 6, ("base!FJ73", "base!FS73", f"{FEMALE}!D2844"), ("+30",)),
    "aemeath_s6_enhanced_skill_trajectory_gain": workbook("aemeath", 6, ("base!FJ73", "base!FS73"), ("10",)),
    "aemeath_s6_tune_response_trajectory_gain": workbook("aemeath", 6, ("base!FJ73", "base!FS73"), (TUNE_RESPONSE, "10")),
    "aemeath_s6_fusion_application_trajectory_gain": workbook("aemeath", 6, ("base!FJ73", "base!FS73"), (FUSION_EFFECT_WHEN, "1")),
    "aemeath_s6_tune_fixed_crit": workbook("aemeath", 6, ("base!FJ73", "base!FS73"), (TUNE, "80%", "175%")),
    "aemeath_s6_fusion_fixed_crit": workbook("aemeath", 6, ("base!FJ73", "base!FS73"), (FUSION, "80%", "175%")),
    "lynae_s1_light_leap_coefficient": workbook("lynae", 1, ("base!FE103", "base!FN103"), ("120%",)),
    "lynae_s1_paint_duration": workbook("lynae", 1, ("base!FE103", "base!FN103"), ("10",)),
    "lynae_s1_paint_application_cadence": workbook("lynae", 1, (f"{FEMALE}!C2683:D2688",), ("120F",)),
    "lynae_s1_pull_diagnostic": {"character_id": "lynae", "sequence": 1, "support_status": "diagnostic_only", "source_type": "bwiki_exact", "url": LYNAE_BWIKI_URL, "tokens": ("6",)},
    "lynae_s1_precombat_overflow": {"character_id": "lynae", "sequence": 1, "support_status": "implemented", "source_type": "bwiki_exact", "url": LYNAE_BWIKI_URL, "tokens": ("120", "2")},
    "lynae_s2_self_deepen": workbook("lynae", 2, ("base!FF103", "base!FO103"), ("25%",)),
    "lynae_s2_outro_deepen": workbook("lynae", 2, ("base!FF103", "base!FO103"), ("14", "25%")),
    "lynae_s2_outro_duration_and_early_end": workbook("lynae", 2, ("base!FF103", "base!FO103"), ("14",)),
    "lynae_s2_collective_interference_cap": workbook("lynae", 2, (f"{FEMALE}!C2728:D2728",), ("C2",)),
    "mornye_s1_marker_duration": workbook("mornye", 1, ("base!FE72", "base!FN72"), ("20",)),
    "mornye_s1_observation_applies_interfered_marker": workbook("mornye", 1, ("base!FE72", "base!FN72"), ("20",)),
    "mornye_s1_marker_amp_formula": workbook("mornye", 1, (f"{FEMALE}!D4164",), ("0.25%", "40%")),
    "mornye_s2_party_crit_damage_formula": workbook("mornye", 2, ("base!FF72", "base!FO72"), ("0.2%", "32%")),
    "mornye_s2_field_off_tune_bonus": workbook("mornye", 2, (f"{FEMALE}!C4122:D4122",), ("50%", "20%")),
    "mornye_s3_concerto_restore": workbook("mornye", 3, ("base!FG72", "base!FP72"), ("25",)),
    "mornye_s3_relative_momentum_restore": workbook("mornye", 3, ("base!FG72", "base!FP72"), ("100",)),
    "mornye_s3_internal_cooldown": workbook("mornye", 3, ("base!FG72", "base!FP72"), ("25",)),
    "mornye_s3_starfield_independent_trigger": {"character_id": "mornye", "sequence": 3, "support_status": "implemented", "source_type": "interpretation", "refs": ("base!FG72", "base!FP72"), "artifact": "data/source/user_account_actual_v120.json", "weapon_artifact": "data/weapons.json", "profile_id": "mornye_account_actual_01", "weapon_id": "starfield_calibrator", "weapon_rank": 5, "tokens": ("25", "100", "16", "20")},
}
