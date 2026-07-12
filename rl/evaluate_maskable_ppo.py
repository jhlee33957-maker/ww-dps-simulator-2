from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from collections import Counter
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.roster import read_party_presets
from simulator.build_profiles import parse_build_profile_overrides, parse_stat_overrides
from simulator.transition_config import (
    build_aemeath_resonance_mode_override,
    build_effective_transition_config,
    build_mornye_expectation_error_mode_override,
    build_mornye_heal_event_mode_override,
    build_transition_mode_overrides,
    load_transition_config,
    mechanics_mode_summary,
    transition_event_counts,
    transition_mode_summary,
)
from rl.evaluation_report import build_generated_damage_summary
from rl.damage_attribution import damage_by_character as event_aware_damage_by_character
from rl.demo_contract import (
    OBSERVATION_SHAPE,
    OBSERVATION_VERSION,
    POLICY_ACTION_COUNT,
    action_data_hash,
    json_safe,
    party_config_hash,
    sequence_hash,
)


METHODOLOGY_PATH = PROJECT_ROOT / "data" / "rl_training_methodology.json"
MANUAL_BASELINE_SUMMARY_PATH = PROJECT_ROOT / "results" / "manual_120s_baseline_v104_summary.json"
OBSERVATION_METADATA_KEYS = (
    "observation_shape",
    "observation_version",
    "observation_labels",
    "max_party_slots",
    "max_policy_action_slots",
    "observation_action_slot_mapping",
)

METADATA_COMPATIBILITY_KEYS = (
    "selected_party_character_ids",
    "initial_active_character",
    "policy_action_ids",
    "policy_action_count",
    "active_build_profiles",
    "effective_build_stats_summary",
    "action_data_hash",
    "party_config_hash",
)


def observation_metadata_mismatches(metadata: dict[str, Any], env: Any) -> dict[str, dict[str, Any]]:
    expected = env.observation_metadata()
    return {
        key: {"model": metadata.get(key), "evaluation": expected[key]}
        for key in OBSERVATION_METADATA_KEYS
        if metadata.get(key) != expected[key]
    }


def bc_metadata_path(model_path: Path) -> Path:
    return Path(str(model_path) + ".bc_metadata.json")


def load_model_metadata(model_path: Path, global_metadata_path: Path) -> dict[str, Any]:
    sidecar_path = bc_metadata_path(model_path)
    if sidecar_path.exists():
        return {
            "source": "model_sidecar",
            "path": sidecar_path,
            "metadata": json.loads(sidecar_path.read_text(encoding="utf-8")),
        }
    if global_metadata_path.exists():
        metadata = json.loads(global_metadata_path.read_text(encoding="utf-8"))
        metadata_model_path = metadata.get("model_path")
        if metadata_model_path and _paths_match(Path(metadata_model_path), model_path):
            return {
                "source": "associated_global",
                "path": global_metadata_path,
                "metadata": metadata,
            }
    return {"source": "none", "path": None, "metadata": {}}


def model_metadata_mismatches(metadata: dict[str, Any], env: Any) -> dict[str, dict[str, Any]]:
    expected = {
        "selected_party_character_ids": env.get_selected_party_character_ids(),
        "initial_active_character": env.get_initial_active_character(),
        "policy_action_ids": env.get_policy_action_ids(),
        "policy_action_count": int(env.action_space.n),
        "active_build_profiles": env.get_active_build_profiles(),
        "effective_build_stats_summary": env.get_effective_build_stats_summary(),
        "action_data_hash": action_data_hash(root=PROJECT_ROOT),
        "party_config_hash": party_config_hash(root=PROJECT_ROOT),
    }
    mismatches = {
        key: {"model": metadata.get(key), "evaluation": value}
        for key, value in expected.items()
        if metadata.get(key) != value
    }
    missing = [key for key in METADATA_COMPATIBILITY_KEYS if key not in metadata]
    for key in missing:
        mismatches[f"missing_{key}"] = {"model": None, "evaluation": expected.get(key)}
    mismatches.update(observation_metadata_mismatches(metadata, env))
    mismatches.update(_stale_contract_mismatches(metadata))
    return mismatches


def _paths_match(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.as_posix() == right.as_posix()


def _stale_contract_mismatches(metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mismatches: dict[str, dict[str, Any]] = {}
    observation_shape = metadata.get("observation_shape")
    observation_version = metadata.get("observation_version")
    policy_action_count = metadata.get("policy_action_count")
    if observation_shape is not None and list(observation_shape) != list(OBSERVATION_SHAPE):
        mismatches["stale_observation_shape"] = {"model": observation_shape, "expected": list(OBSERVATION_SHAPE)}
    if observation_version is not None and observation_version != OBSERVATION_VERSION:
        mismatches["stale_observation_version"] = {"model": observation_version, "expected": OBSERVATION_VERSION}
    if policy_action_count is not None and int(policy_action_count) != POLICY_ACTION_COUNT:
        mismatches["stale_policy_action_count"] = {"model": policy_action_count, "expected": POLICY_ACTION_COUNT}
    return mismatches


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a trained Maskable PPO model.")
    parser.add_argument("--model-path", type=Path, default=PROJECT_ROOT / "models" / "maskable_ppo_wuwa.zip")
    parser.add_argument("--character-ids", type=str, default=None)
    parser.add_argument("--party-character-ids", type=str, default=None)
    parser.add_argument("--party", type=str, default=None)
    parser.add_argument(
        "--build-profile",
        action="append",
        default=[],
        help="Build profile override in character_id:profile_id form. May be repeated.",
    )
    parser.add_argument(
        "--stat",
        action="append",
        default=[],
        help="Quick stat override in character_id:field:value form. May be repeated.",
    )
    parser.add_argument("--initial-active-character", type=str, default=None)
    parser.add_argument("--transition-mode", choices=["disabled", "dry_run", "enabled"], default=None)
    parser.add_argument("--aemeath-qte-mode", choices=["disabled", "dry_run", "enabled"], default=None)
    parser.add_argument("--mornye-intro-mode", choices=["disabled", "dry_run", "enabled"], default=None)
    parser.add_argument(
        "--mornye-expectation-error-mode",
        choices=["expectation_error_only", "dry_run_success_candidate", "always_success"],
        default=None,
    )
    parser.add_argument(
        "--aemeath-resonance-mode",
        choices=["fusion_burst", "tune_rupture", "unresolved"],
        default=None,
    )
    parser.add_argument(
        "--mornye-heal-event-mode",
        choices=["disabled", "field_creation_only", "simplified_syntony_field_uptime"],
        default=None,
    )
    parser.add_argument("--allow-mismatch", action="store_true")
    parser.add_argument("--dry-run-contract", action="store_true")
    parser.add_argument(
        "--training-metadata-path",
        type=Path,
        default=PROJECT_ROOT / "results" / "training_metadata.json",
        help="Legacy global metadata fallback. A model sidecar is preferred when present.",
    )
    parser.add_argument("--diagnose-policy-probs", action="store_true")
    parser.add_argument(
        "--write-policy-probability-report",
        type=Path,
        default=PROJECT_ROOT / "reports" / "aemeath_mornye_lynae_policy_probability_report.json",
    )
    parser.add_argument("--summary-path", type=Path, default=PROJECT_ROOT / "results" / "ppo_evaluation_summary.json")
    parser.add_argument("--timeline-path", type=Path, default=PROJECT_ROOT / "results" / "ppo_timeline.csv")
    return parser


def parse_args() -> argparse.Namespace:
    return build_arg_parser().parse_args()


def build_effective_config_from_args(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any] | None]:
    party_presets = read_party_presets(PROJECT_ROOT / "data")
    party_preset = party_presets.get(args.party) if args.party else None
    cli_overrides = build_transition_mode_overrides(
        transition_mode=args.transition_mode,
        aemeath_qte_mode=args.aemeath_qte_mode,
        mornye_intro_mode=args.mornye_intro_mode,
    )
    for mechanic_overrides in (
        build_aemeath_resonance_mode_override(args.aemeath_resonance_mode),
        build_mornye_expectation_error_mode_override(args.mornye_expectation_error_mode),
        build_mornye_heal_event_mode_override(args.mornye_heal_event_mode),
    ):
        _deep_update(cli_overrides, mechanic_overrides)
    if not cli_overrides.get("characters") and not cli_overrides.get("mechanics"):
        cli_overrides = None
    config = build_effective_transition_config(
        load_transition_config(PROJECT_ROOT / "data"),
        party_preset,
        cli_overrides=cli_overrides,
    )
    return config, party_preset


def main() -> None:
    args = parse_args()
    if not args.model_path.exists():
        print(f"No trained PPO model found at {args.model_path}.")
        print("Run training first: python rl/train_maskable_ppo.py --timesteps 50000")
        raise SystemExit(1)

    try:
        from sb3_contrib import MaskablePPO
    except ModuleNotFoundError:
        print("Missing RL dependency. Run: pip install -r requirements.txt")
        raise SystemExit(1) from None

    from rl.evaluate_utils import action_count_breakdown, run_masked_episode

    transition_config, party_preset = build_effective_config_from_args(args)
    try:
        build_profile_overrides = parse_build_profile_overrides(args.build_profile)
        stat_overrides = parse_stat_overrides(args.stat)
    except ValueError as exc:
        print(f"Invalid build/stat override: {exc}")
        raise SystemExit(2) from None
    from env.wuwa_env import WuwaDpsEnv

    metadata_env = WuwaDpsEnv(
        PROJECT_ROOT / "data",
        selected_character_ids=args.character_ids or args.party_character_ids,
        party=args.party,
        initial_active_character=args.initial_active_character,
        transition_config=transition_config,
        build_profile_overrides=build_profile_overrides,
        stat_overrides=stat_overrides,
    )
    validation = metadata_env.simulation.validate_build_profiles()
    if not validation.get("ok", False):
        print("Build profile validation failed.")
        for error in validation.get("errors", []):
            print(f"- {error}")
        raise SystemExit(2)
    for warning in validation.get("warnings", []):
        print(f"Build profile warning: {warning}")
    metadata_info = load_model_metadata(args.model_path, args.training_metadata_path)
    metadata: dict[str, Any] = metadata_info["metadata"]
    metadata_mismatches: dict[str, Any] = {}
    if metadata:
        metadata_mismatches = model_metadata_mismatches(metadata, metadata_env)
        if metadata_mismatches and not args.allow_mismatch:
            print(
                "Model metadata does not match the requested evaluation roster, build profile config, "
                "or observation contract."
            )
            print(json.dumps(json_safe(metadata_mismatches), indent=2, ensure_ascii=False))
            print("Use --allow-mismatch only if you intentionally want to bypass this check.")
            raise SystemExit(1)
        if metadata_mismatches:
            print("WARNING: evaluating with model metadata mismatches:")
            print(json.dumps(json_safe(metadata_mismatches), indent=2, ensure_ascii=False))
    model = MaskablePPO.load(args.model_path)
    model_space_mismatches = _model_space_mismatches(model, metadata_env)
    if model_space_mismatches and not args.allow_mismatch:
        print("Model spaces do not match the requested evaluation environment.")
        print(json.dumps(json_safe(model_space_mismatches), indent=2, ensure_ascii=False))
        raise SystemExit(1)
    if args.dry_run_contract:
        print(
            json.dumps(
                json_safe(
                    {
                        "status": "ok",
                        "dry_run_contract": True,
                        "model_path": args.model_path,
                        "metadata_source": metadata_info["source"],
                        "metadata_path": metadata_info["path"],
                        "metadata_mismatches": metadata_mismatches,
                        "model_space_mismatches": model_space_mismatches,
                    }
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    env, action_sequence, resolved_action_sequence = run_masked_episode(
        model,
        PROJECT_ROOT / "data",
        deterministic=True,
        selected_character_ids=args.character_ids or args.party_character_ids,
        party=args.party,
        initial_active_character=args.initial_active_character,
        transition_config=transition_config,
        build_profile_overrides=build_profile_overrides,
        stat_overrides=stat_overrides,
    )
    summary = env.simulation.summary()
    counts = action_count_breakdown(action_sequence)
    resolved_counts = action_count_breakdown(resolved_action_sequence)
    selected_counts_by_character_prefix = _action_counts_by_character_prefix(action_sequence)
    resolved_counts_by_character_prefix = _action_counts_by_character_prefix(resolved_action_sequence)
    policy_action_exposed_by_character = _policy_actions_exposed_by_character(
        env.get_policy_action_ids(),
        env.simulation.actions,
        env.get_selected_party_character_ids(),
    )
    damage_by_action: Counter[str] = Counter()
    damage_by_resolved: Counter[str] = Counter()
    damage_by_category: Counter[str] = Counter()
    damage_by_action_type: Counter[str] = Counter()
    damage_by_damage_bonus_category: Counter[str] = Counter()
    for selected_id, resolved_id, row in zip(action_sequence, resolved_action_sequence, summary.timeline):
        damage_by_action[selected_id] += row.total_action_damage
        damage_by_resolved[resolved_id] += row.total_action_damage
        damage_by_category[row.damage_category] += row.total_action_damage
        damage_by_action_type[row.action_type or "other"] += row.total_action_damage
        damage_by_damage_bonus_category[row.damage_bonus_category or row.damage_category] += row.total_action_damage
    damage_by_character = event_aware_damage_by_character(summary.timeline, total_damage=summary.total_damage)
    generated_damage_summary = build_generated_damage_summary(
        summary.timeline,
        total_damage=summary.total_damage,
    )
    manual_baseline_parity = _manual_baseline_parity(
        action_sequence=action_sequence,
        resolved_action_sequence=resolved_action_sequence,
        total_damage=summary.total_damage,
        dps=summary.dps,
        damage_by_character=damage_by_character,
    )
    training_methodology_summary = _load_training_methodology_summary()
    unused_party_members = [
        character_id
        for character_id in env.get_selected_party_character_ids()
        if selected_counts_by_character_prefix.get(character_id, 0) == 0
        and resolved_counts_by_character_prefix.get(character_id, 0) == 0
        and damage_by_character.get(character_id, 0.0) == 0.0
    ]
    valid_action_exposure_note = (
        "Transition actions are not policy actions. PPO selects policy-visible actions such as "
        "swap_to_lynae; full-Concerto transition execution is visible in resolved_action_counts."
    )

    print("Selected party:", env.get_selected_party_character_ids())
    print("Initial active character:", env.get_initial_active_character())
    print("Policy action IDs:", env.get_policy_action_ids())
    print(f"Total damage: {summary.total_damage:.2f}")
    print(f"DPS: {summary.dps:.2f}")
    print(f"Final combat time: {summary.final_time:.2f}")
    print(f"Final action time: {summary.final_action_time:.2f}")
    print("Selected action sequence:", ", ".join(action_sequence))
    print("Action count breakdown:", counts)
    print("Resolved action count breakdown:", resolved_counts)
    print("Selected action counts:", counts)
    print("Resolved action counts:", resolved_counts)
    print("Selected action counts by character prefix:", selected_counts_by_character_prefix)
    print("Resolved action counts by character prefix:", resolved_counts_by_character_prefix)
    print("Policy action exposed by character:", policy_action_exposed_by_character)
    print("Unused party members:", unused_party_members)
    print("Valid action exposure note:", valid_action_exposure_note)
    print("Damage by selected action:", dict(damage_by_action))
    print("Damage by resolved action:", dict(damage_by_resolved))
    print("Damage by character:", dict(damage_by_character))
    print("Damage by category:", dict(damage_by_category))
    print("Damage by action type:", dict(damage_by_action_type))
    print("Damage by damage bonus category:", dict(damage_by_damage_bonus_category))
    print(
        "Generated mechanic damage:",
        {
            "total": generated_damage_summary["generated_mechanic_damage_total"],
            "share": generated_damage_summary["generated_mechanic_damage_share_of_total"],
            "aemeath_forte": generated_damage_summary["aemeath_forte_generated_damage_total"],
            "seraphic_duet_followup": generated_damage_summary[
                "aemeath_seraphic_duet_followup_damage_total"
            ],
        },
    )
    print("Aemeath Resonance Mode:", summary.aemeath_resonance_mode)
    print("Mechanic event emitted counts:", summary.mechanic_event_emitted_counts)
    print("Resource summary:", summary.resources)
    print("Timeline:")
    for row in summary.timeline:
        print(json.dumps(json_safe(row.model_dump()), ensure_ascii=True))

    results_dir = args.summary_path.parent
    results_dir.mkdir(parents=True, exist_ok=True)
    args.timeline_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path = args.summary_path
    timeline_path = args.timeline_path

    summary_payload = {
        "total_damage": summary.total_damage,
        "dps": summary.dps,
        "final_time": summary.final_time,
        "final_action_time": summary.final_action_time,
        "active_character": summary.active_character,
        "selected_character_ids": env.get_selected_character_ids(),
        "selected_party_character_ids": env.get_selected_party_character_ids(),
        "selected_party_id": env.get_party_id() or args.party,
        "party_id": env.get_party_id() or args.party,
        "party_members": env.get_selected_party_character_ids(),
        "initial_active_character": env.get_initial_active_character(),
        "policy_action_ids": env.get_policy_action_ids(),
        "transition_modes": transition_mode_summary(transition_config),
        "mechanics_modes": mechanics_mode_summary(transition_config),
        "aemeath_resonance_mode": summary.aemeath_resonance_mode,
        "aemeath_resonance_mode_source": summary.aemeath_resonance_mode_source,
        "mornye_heal_event_mode": summary.mornye_heal_event_mode,
        "mornye_heal_event_mode_source": summary.mornye_heal_event_mode_source,
        "mechanic_event_trigger_action_ids": summary.mechanic_event_trigger_action_ids,
        "mechanic_event_transition_trigger_action_ids": summary.mechanic_event_transition_trigger_action_ids,
        "mechanic_event_emitted_counts": summary.mechanic_event_emitted_counts,
        "fusion_burst_event_count": summary.fusion_burst_event_count,
        "tune_rupture_shifting_event_count": summary.tune_rupture_shifting_event_count,
        "mechanic_event_unresolved_reason": summary.mechanic_event_unresolved_reason,
        "unsupported_aemeath_followup_mechanics": summary.unsupported_aemeath_followup_mechanics,
        "active_echo_sets": summary.active_echo_sets,
        "active_weapons": summary.active_weapons,
        "weapon_effects_enabled": summary.weapon_effects_enabled,
        "weapon_effect_trigger_counts": summary.weapon_effect_trigger_counts,
        "weapon_effect_source_status": summary.weapon_effect_source_status,
        "starfield_calibrator_concerto_restore_trigger_count": (
            summary.starfield_calibrator_concerto_restore_trigger_count
        ),
        "starfield_calibrator_concerto_restored_total": summary.starfield_calibrator_concerto_restored_total,
        "starfield_calibrator_party_crit_damage_trigger_count": (
            summary.starfield_calibrator_party_crit_damage_trigger_count
        ),
        "starfield_calibrator_party_crit_damage_uptime_seconds": (
            summary.starfield_calibrator_party_crit_damage_uptime_seconds
        ),
        "starfield_calibrator_party_crit_damage_bonus": summary.starfield_calibrator_party_crit_damage_bonus,
        "weapon_effect_cooldown_blocked_counts": summary.weapon_effect_cooldown_blocked_counts,
        "discord_concerto_restore_support_status": summary.discord_concerto_restore_support_status,
        "echo_set_active_buffs": summary.echo_set_active_buffs,
        "aemeath_trailblazing_star_5set_enabled": summary.aemeath_trailblazing_star_5set_enabled,
        "aemeath_trailblazing_star_5set_trigger_event_tags": (
            summary.aemeath_trailblazing_star_5set_trigger_event_tags
        ),
        "aemeath_trailblazing_star_5set_trigger_count": summary.aemeath_trailblazing_star_5set_trigger_count,
        "aemeath_trailblazing_star_5set_uptime_seconds": summary.aemeath_trailblazing_star_5set_uptime_seconds,
        "aemeath_trailblazing_star_5set_buff_windows": summary.aemeath_trailblazing_star_5set_buff_windows,
        "high_syntony_field_active": summary.high_syntony_field_active,
        "high_syntony_field_remaining": summary.high_syntony_field_remaining,
        "high_syntony_field_created_count": summary.high_syntony_field_created_count,
        "high_syntony_field_def_bonus_active": summary.high_syntony_field_def_bonus_active,
        "high_syntony_field_def_percent_bonus": summary.high_syntony_field_def_percent_bonus,
        "high_syntony_field_off_tune_inherited": summary.high_syntony_field_off_tune_inherited,
        "high_syntony_field_heal_proxy_active": summary.high_syntony_field_heal_proxy_active,
        "high_syntony_field_healing_multiplier_bonus": summary.high_syntony_field_healing_multiplier_bonus,
        "critical_protocol_high_syntony_created_before_damage": (
            summary.critical_protocol_high_syntony_created_before_damage
        ),
        "high_syntony_field_same_action_application": summary.high_syntony_field_same_action_application,
        "high_syntony_field_application_timing": summary.high_syntony_field_application_timing,
        "runtime_def_percent_bonus": summary.runtime_def_percent_bonus,
        "current_off_tune_buildup_rate": summary.current_off_tune_buildup_rate,
        "enemy_off_tune_current": summary.enemy_off_tune_current,
        "enemy_off_tune_max": summary.enemy_off_tune_max,
        "enemy_mistune_active": summary.enemy_mistune_active,
        "enemy_tune_break_available": summary.enemy_tune_break_available,
        "enemy_tune_break_cooldown_seconds": summary.enemy_tune_break_cooldown_seconds,
        "enemy_tune_break_cooldown_source_status": summary.enemy_tune_break_cooldown_source_status,
        "enemy_tune_break_cooldown_source_ref": summary.enemy_tune_break_cooldown_source_ref,
        "enemy_tune_break_cooldown_remaining": summary.enemy_tune_break_cooldown_remaining,
        "off_tune_accumulation_blocked_by_tune_break_cooldown_count": (
            summary.off_tune_accumulation_blocked_by_tune_break_cooldown_count
        ),
        "mapped_off_tune_action_count": summary.mapped_off_tune_action_count,
        "unmapped_off_tune_action_ids": summary.unmapped_off_tune_action_ids,
        "unresolved_off_tune_damaging_action_ids": summary.unresolved_off_tune_damaging_action_ids,
        "off_tune_mapping_completeness_status": summary.off_tune_mapping_completeness_status,
        "off_tune_value_mapping_source_report": summary.off_tune_value_mapping_source_report,
        "tune_break_action_available_ids": summary.tune_break_action_available_ids,
        "tune_break_action_used_count": summary.tune_break_action_used_count,
        "tune_break_damage_total": summary.tune_break_damage_total,
        "tune_response_damage_total": summary.tune_response_damage_total,
        "aemeath_starburst_damage_total": summary.aemeath_starburst_damage_total,
        "mornye_particle_jet_damage_total": summary.mornye_particle_jet_damage_total,
        "aemeath_starburst_trigger_count": summary.aemeath_starburst_trigger_count,
        "mornye_particle_jet_trigger_count": summary.mornye_particle_jet_trigger_count,
        "aemeath_starburst_cooldown_blocked_count": summary.aemeath_starburst_cooldown_blocked_count,
        "mornye_particle_jet_cooldown_blocked_count": summary.mornye_particle_jet_cooldown_blocked_count,
        "tune_response_damage_formula_source_status": summary.tune_response_damage_formula_source_status,
        "tune_response_event_order_source_status": summary.tune_response_event_order_source_status,
        "tune_break_damage_receives_new_interfered_marker_amp": (
            summary.tune_break_damage_receives_new_interfered_marker_amp
        ),
        "response_damage_receives_interfered_marker_amp": summary.response_damage_receives_interfered_marker_amp,
        "response_damage_receives_newly_applied_interfered_marker_amp": (
            summary.response_damage_receives_newly_applied_interfered_marker_amp
        ),
        "response_damage_receives_existing_interfered_marker_amp": (
            summary.response_damage_receives_existing_interfered_marker_amp
        ),
        "response_damage_receives_new_interfered_marker_amp": (
            summary.response_damage_receives_new_interfered_marker_amp
        ),
        "target_tune_shift_state": summary.target_tune_shift_state,
        "target_interfered_state": summary.target_interfered_state,
        "interfered_marker_damage_taken_amp": summary.interfered_marker_damage_taken_amp,
        "unresolved_response_damage_events": summary.unresolved_response_damage_events,
        "halo_of_starry_radiance_5set_active": summary.halo_of_starry_radiance_5set_active,
        "halo_of_starry_radiance_5set_atk_percent_bonus": summary.halo_of_starry_radiance_5set_atk_percent_bonus,
        "halo_atk_buff_does_not_affect_mornye_def_damage": summary.halo_atk_buff_does_not_affect_mornye_def_damage,
        "high_syntony_field_unavailable_reason": summary.high_syntony_field_unavailable_reason,
        "active_build_profiles": env.get_active_build_profiles(),
        "active_party_build_profiles": env.get_active_build_profiles(),
        "effective_build_stats_summary": env.get_effective_build_stats_summary(),
        "build_profile_validation": validation,
        "stat_overrides": stat_overrides,
        "transition_config_source": transition_config.get("_transition_config_source", ["default"]),
        "party_preset": party_preset.get("party_id") if party_preset else None,
        "observation_shape": list(env.observation_space.shape),
        "observation_version": env.observation_version,
        "deprecated_observation_version": env.observation_metadata()["deprecated_observation_version"],
        "observation_labels": env.observation_labels(),
        "observation_channel_mapping": env.observation_channel_mapping(),
        "observation_slot_mapping": env.observation_slot_mapping(),
        "observation_action_slot_mapping": env.observation_action_slot_mapping(),
        "max_party_slots": env.observation_metadata()["max_party_slots"],
        "max_policy_action_slots": env.observation_metadata()["max_policy_action_slots"],
        "curriculum_reset_mode": env.get_last_curriculum_reset_mode(),
        "training_methodology_summary": training_methodology_summary,
        "model_training_metadata_source": metadata_info["source"],
        "model_training_metadata_path": metadata_info["path"].as_posix() if metadata_info["path"] else None,
        "model_training_metadata": metadata if metadata else None,
        "model_metadata_mismatches": metadata_mismatches,
        "model_space_mismatches": model_space_mismatches,
        "model_observation_shape": metadata.get("observation_shape") if metadata else None,
        "current_observation_shape": list(env.observation_space.shape),
        "observation_shape_matches_model": (
            metadata.get("observation_shape") == list(env.observation_space.shape) if metadata else None
        ),
        **transition_event_counts(summary.timeline),
        "action_sequence": action_sequence,
        "resolved_action_sequence": resolved_action_sequence,
        "selected_action_count": len(action_sequence),
        "resolved_action_count": len(resolved_action_sequence),
        **manual_baseline_parity,
        "action_counts": counts,
        "selected_action_counts": counts,
        "resolved_action_counts": resolved_counts,
        "selected_action_counts_by_character_prefix": selected_counts_by_character_prefix,
        "resolved_action_counts_by_character_prefix": resolved_counts_by_character_prefix,
        "policy_action_exposed_by_character": policy_action_exposed_by_character,
        "unused_party_members": unused_party_members,
        "valid_action_exposure_note": valid_action_exposure_note,
        "damage_by_selected_action": dict(damage_by_action),
        "damage_by_policy_action": dict(damage_by_action),
        "damage_by_resolved_action": dict(damage_by_resolved),
        "damage_by_character": dict(damage_by_character),
        "damage_by_category": dict(damage_by_category),
        "damage_by_action_type": dict(damage_by_action_type),
        "damage_by_damage_bonus_category": dict(damage_by_damage_bonus_category),
        **generated_damage_summary,
        "damage_bonus_breakdown_sample": [
            {
                "selected_action_id": row.selected_action_id,
                "resolved_action_id": row.resolved_action_id,
                "character_id": row.actor_character_id or row.character_id,
                "action_type": row.action_type,
                "damage_category": row.damage_category,
                "damage_bonus_category": row.damage_bonus_category,
                "damage_element": row.damage_element,
                "raw_skill_category": row.raw_skill_category,
                "raw_damage_type": row.raw_damage_type,
                "all_dmg_bonus": row.all_dmg_bonus,
                "category_dmg_bonus": row.category_dmg_bonus,
                "element_dmg_bonus": row.element_dmg_bonus,
                "runtime_element_damage_bonus": row.runtime_element_damage_bonus,
                "echo_set_damage_bonus": row.echo_set_damage_bonus,
                "effective_damage_bonus": row.effective_damage_bonus,
                "crit_rate_before_buffs": row.crit_rate_before_buffs,
                "crit_rate_after_buffs": row.crit_rate_after_buffs,
                "crit_damage_before_buffs": row.crit_damage_before_buffs,
                "crit_damage_after_buffs": row.crit_damage_after_buffs,
                "runtime_crit_damage_bonus": row.runtime_crit_damage_bonus,
                "weapon_effect_triggered": row.weapon_effect_triggered,
                "weapon_id": row.weapon_id,
                "weapon_rank": row.weapon_rank,
                "weapon_effect_id": row.weapon_effect_id,
                "weapon_effect_resource": row.weapon_effect_resource,
                "weapon_effect_source_status": row.weapon_effect_source_status,
                "concerto_energy_restored_by_weapon": row.concerto_energy_restored_by_weapon,
                "weapon_effect_cooldown_blocked": row.weapon_effect_cooldown_blocked,
                "starfield_calibrator_party_crit_damage_active": (
                    row.starfield_calibrator_party_crit_damage_active
                ),
                "starfield_calibrator_party_crit_damage_bonus": row.starfield_calibrator_party_crit_damage_bonus,
                "echo_set_triggered_buff_ids": row.echo_set_triggered_buff_ids,
                "echo_set_buff_refreshed": row.echo_set_buff_refreshed,
                "aemeath_trailblazing_star_5set_active": row.aemeath_trailblazing_star_5set_active,
                "aemeath_trailblazing_star_5set_applied_before_triggering_damage": (
                    row.aemeath_trailblazing_star_5set_applied_before_triggering_damage
                ),
                "trailblazing_star_5set_same_action_application": row.trailblazing_star_5set_same_action_application,
                "trailblazing_star_5set_application_timing": row.trailblazing_star_5set_application_timing,
                "high_syntony_field_active": row.high_syntony_field_active,
                "high_syntony_field_remaining": row.high_syntony_field_remaining,
                "high_syntony_field_def_bonus_active": row.high_syntony_field_def_bonus_active,
                "high_syntony_field_def_percent_bonus": row.high_syntony_field_def_percent_bonus,
                "high_syntony_field_off_tune_inherited": row.high_syntony_field_off_tune_inherited,
                "high_syntony_field_heal_proxy_active": row.high_syntony_field_heal_proxy_active,
                "critical_protocol_high_syntony_created_before_damage": (
                    row.critical_protocol_high_syntony_created_before_damage
                ),
                "high_syntony_field_same_action_application": row.high_syntony_field_same_action_application,
                "high_syntony_field_application_timing": row.high_syntony_field_application_timing,
                "runtime_def_percent_bonus": row.runtime_def_percent_bonus,
                "current_off_tune_buildup_rate": row.current_off_tune_buildup_rate,
                "off_tune_value_source_status": row.off_tune_value_source_status,
                "off_tune_value_source_ref": row.off_tune_value_source_ref,
                "off_tune_accumulation_blocked_by_tune_break_cooldown": (
                    row.off_tune_accumulation_blocked_by_tune_break_cooldown
                ),
                "enemy_off_tune_current_after": row.enemy_off_tune_current_after,
                "enemy_tune_break_available": row.enemy_tune_break_available,
                "enemy_tune_break_cooldown_seconds": row.enemy_tune_break_cooldown_seconds,
                "enemy_tune_break_cooldown_source_status": row.enemy_tune_break_cooldown_source_status,
                "tune_break_action_available_ids": row.tune_break_action_available_ids,
                "target_tune_shift_state": row.target_tune_shift_state,
                "target_interfered_state": row.target_interfered_state,
                "interfered_marker_damage_taken_amp": row.interfered_marker_damage_taken_amp,
                "tune_response_damage": row.tune_response_damage,
                "aemeath_starburst_response_damage": row.aemeath_starburst_response_damage,
                "mornye_particle_jet_response_damage": row.mornye_particle_jet_response_damage,
                "mornye_particle_jet_multiplier_used": row.mornye_particle_jet_multiplier_used,
                "mornye_particle_jet_constellation_variant": row.mornye_particle_jet_constellation_variant,
                "response_damage_receives_interfered_marker_amp": row.response_damage_receives_interfered_marker_amp,
                "response_damage_receives_newly_applied_interfered_marker_amp": (
                    row.response_damage_receives_newly_applied_interfered_marker_amp
                ),
                "response_damage_receives_existing_interfered_marker_amp": (
                    row.response_damage_receives_existing_interfered_marker_amp
                ),
                "response_damage_receives_new_interfered_marker_amp": (
                    row.response_damage_receives_new_interfered_marker_amp
                ),
                "unresolved_response_damage_events": row.unresolved_response_damage_events,
                "halo_of_starry_radiance_5set_active": row.halo_of_starry_radiance_5set_active,
                "halo_of_starry_radiance_5set_atk_percent_bonus": (
                    row.halo_of_starry_radiance_5set_atk_percent_bonus
                ),
                "halo_atk_buff_does_not_affect_mornye_def_damage": row.halo_atk_buff_does_not_affect_mornye_def_damage,
                "build_profile_id": row.build_profile_id,
                "damage": row.total_action_damage,
            }
            for row in summary.timeline[:20]
        ],
        "resources": summary.resources,
    }
    summary_path.write_text(json.dumps(json_safe(summary_payload), indent=2, ensure_ascii=False), encoding="utf-8")

    timeline_rows = [row.model_dump() for row in summary.timeline]
    with timeline_path.open("w", newline="", encoding="utf-8") as file:
        if timeline_rows:
            writer = csv.DictWriter(file, fieldnames=list(timeline_rows[0]))
            writer.writeheader()
            writer.writerows(timeline_rows)

    print(f"Saved evaluation summary to {summary_path}")
    print(f"Saved timeline to {timeline_path}")
    if args.diagnose_policy_probs:
        from scripts.aemeath_mornye_lynae_policy_probability_diagnostic import run_policy_probability_diagnostic

        probability_report = run_policy_probability_diagnostic(
            model_path=args.model_path,
            party=args.party or "aemeath_mornye_lynae_enabled_test_party",
            write_json=args.write_policy_probability_report,
        )
        print(f"Saved policy probability diagnostic to {args.write_policy_probability_report}")
        print("Policy probability diagnostic status:", probability_report["model_probability_status"])


def _deep_update(target: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
    return target


def _action_character_prefix(action_id: str) -> str:
    if action_id.startswith("transition:"):
        action_id = action_id.split(":", 1)[1]
    if action_id.startswith("swap_to_"):
        return action_id.removeprefix("swap_to_")
    return action_id.split("_", 1)[0] if "_" in action_id else action_id


def _action_counts_by_character_prefix(action_sequence: list[str]) -> dict[str, int]:
    return dict(Counter(_action_character_prefix(action_id) for action_id in action_sequence))


def _manual_baseline_parity(
    *,
    action_sequence: list[str],
    resolved_action_sequence: list[str],
    total_damage: float,
    dps: float,
    damage_by_character: dict[str, float],
) -> dict[str, Any]:
    if not MANUAL_BASELINE_SUMMARY_PATH.exists():
        raise FileNotFoundError(f"Manual baseline summary not found: {MANUAL_BASELINE_SUMMARY_PATH}")
    baseline = json.loads(MANUAL_BASELINE_SUMMARY_PATH.read_text(encoding="utf-8"))
    for key in (
        "selected_sequence_sha256",
        "resolved_sequence_sha256",
        "total_damage",
        "dps",
        "damage_by_character",
    ):
        if key not in baseline:
            raise ValueError(f"Manual baseline summary is missing required key {key!r}")
    selected_sha = sequence_hash(action_sequence)
    resolved_sha = sequence_hash(resolved_action_sequence)
    baseline_total_damage = float(baseline["total_damage"])
    baseline_dps = float(baseline["dps"])
    damage_delta = float(total_damage) - baseline_total_damage
    baseline_damage = {str(key): float(value) for key, value in baseline["damage_by_character"].items()}
    character_damage_match = set(damage_by_character) == set(baseline_damage) and all(
        abs(float(damage_by_character[key]) - baseline_damage[key]) <= 1e-6
        for key in baseline_damage
    )
    return {
        "selected_sequence_sha256": selected_sha,
        "resolved_sequence_sha256": resolved_sha,
        "manual_baseline_total_damage": baseline_total_damage,
        "manual_baseline_dps": baseline_dps,
        "manual_baseline_damage_ratio": float(total_damage) / baseline_total_damage if baseline_total_damage else None,
        "manual_baseline_damage_delta": damage_delta,
        "manual_baseline_selected_sequence_match": selected_sha == baseline["selected_sequence_sha256"],
        "manual_baseline_resolved_sequence_match": resolved_sha == baseline["resolved_sequence_sha256"],
        "manual_baseline_character_damage_match": character_damage_match,
    }


def _policy_actions_exposed_by_character(
    policy_action_ids: list[str],
    actions_by_id: dict[str, Any],
    party_members: list[str],
) -> dict[str, list[str]]:
    exposed = {character_id: [] for character_id in party_members}
    for action_id in policy_action_ids:
        action = actions_by_id.get(action_id)
        character_id = getattr(action, "character_id", None) if action is not None else None
        if action_id.startswith("swap_to_"):
            character_id = action_id.removeprefix("swap_to_")
        if character_id in exposed:
            exposed[character_id].append(action_id)
    return {character_id: sorted(action_ids) for character_id, action_ids in exposed.items()}


def _model_space_mismatches(model: Any, env: Any) -> dict[str, Any]:
    mismatches: dict[str, Any] = {}
    model_action_n = getattr(getattr(model, "action_space", None), "n", None)
    if model_action_n != env.action_space.n:
        mismatches["action_space_n"] = {"model": model_action_n, "evaluation": env.action_space.n}
    model_observation_shape = list(getattr(getattr(model, "observation_space", None), "shape", []) or [])
    env_observation_shape = list(env.observation_space.shape)
    if model_observation_shape != env_observation_shape:
        mismatches["observation_shape"] = {
            "model": model_observation_shape,
            "evaluation": env_observation_shape,
        }
    return mismatches


def _load_training_methodology_summary() -> dict[str, Any]:
    if not METHODOLOGY_PATH.exists():
        return {
            "methodology_summary_id": "missing",
            "algorithm": "MaskablePPO",
            "reward_formula": "damage_this_action / 10000.0",
            "evaluation_default": "none",
        }
    data = json.loads(METHODOLOGY_PATH.read_text(encoding="utf-8"))
    return {
        "methodology_version": data.get("methodology_version"),
        "methodology_summary_id": data.get("methodology_summary_id"),
        "algorithm": data.get("algorithm"),
        "reward_formula": data.get("reward_formula"),
        "evaluation_default": data.get("evaluation_default"),
        "no_character_specific_usage_reward_bonus": data.get("no_character_specific_usage_reward_bonus"),
        "curriculum_training_only_note": data.get("curriculum_training_only_note"),
        "stale_model_warning": data.get("stale_model_warning"),
    }


if __name__ == "__main__":
    main()
