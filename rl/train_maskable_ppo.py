from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.roster import read_party_presets
from simulator.build_profiles import parse_build_profile_overrides, parse_stat_overrides
from simulator.mechanic_events import mechanic_event_metadata_for_config
from simulator.transition_config import (
    build_aemeath_resonance_mode_override,
    build_effective_transition_config,
    build_mornye_expectation_error_mode_override,
    build_mornye_heal_event_mode_override,
    build_transition_mode_overrides,
    load_transition_config,
    mechanics_mode_summary,
    transition_mode_summary,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train Maskable PPO for the Wuwa DPS simulator.")
    parser.add_argument("--timesteps", type=int, default=50_000)
    parser.add_argument("--model-path", type=Path, default=PROJECT_ROOT / "models" / "maskable_ppo_wuwa.zip")
    parser.add_argument("--seed", type=int, default=42)
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
    try:
        from stable_baselines3.common.env_checker import check_env
        from sb3_contrib import MaskablePPO
        from env.wuwa_env import WuwaDpsEnv
    except ModuleNotFoundError:
        print("Missing RL dependency. Run: pip install -r requirements.txt")
        raise SystemExit(1) from None

    transition_config, party_preset = build_effective_config_from_args(args)
    try:
        build_profile_overrides = parse_build_profile_overrides(args.build_profile)
        stat_overrides = parse_stat_overrides(args.stat)
    except ValueError as exc:
        print(f"Invalid build/stat override: {exc}")
        raise SystemExit(2) from None
    env = WuwaDpsEnv(
        PROJECT_ROOT / "data",
        selected_character_ids=args.character_ids or args.party_character_ids,
        party=args.party,
        initial_active_character=args.initial_active_character,
        transition_config=transition_config,
        build_profile_overrides=build_profile_overrides,
        stat_overrides=stat_overrides,
    )
    validation = env.simulation.validate_build_profiles()
    if not validation.get("ok", False):
        print("Build profile validation failed.")
        for error in validation.get("errors", []):
            print(f"- {error}")
        raise SystemExit(2)
    for warning in validation.get("warnings", []):
        print(f"Build profile warning: {warning}")

    try:
        check_env(env, warn=True)
    except Exception as exc:  # check_env is useful, but training should still show the real failure if any.
        print(f"Environment check warning: {exc}")

    model = MaskablePPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        gamma=0.999,
        n_steps=512,
        batch_size=64,
        ent_coef=0.01,
        verbose=1,
        seed=args.seed,
    )
    model.learn(total_timesteps=args.timesteps)

    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.model_path)
    mechanic_event_metadata = mechanic_event_metadata_for_config(transition_config.get("mechanics"))
    training_summary = env.simulation.summary()

    metadata: dict[str, Any] = {
        "algorithm": "MaskablePPO",
        "policy": "MlpPolicy",
        "timesteps": args.timesteps,
        "seed": args.seed,
        "model_path": str(args.model_path),
        "selected_character_ids": env.get_selected_character_ids(),
        "selected_party_character_ids": env.get_selected_party_character_ids(),
        "selected_party_id": env.get_party_id() or args.party,
        "party_id": env.get_party_id() or args.party,
        "party_members": env.get_selected_party_character_ids(),
        "initial_active_character": env.get_initial_active_character(),
        "policy_action_ids": env.get_policy_action_ids(),
        "transition_modes": transition_mode_summary(transition_config),
        "mechanics_modes": mechanics_mode_summary(transition_config),
        "aemeath_resonance_mode": mechanic_event_metadata["aemeath_resonance_mode"],
        "aemeath_resonance_mode_source": mechanic_event_metadata["aemeath_resonance_mode_source"],
        "mornye_heal_event_mode": training_summary.mornye_heal_event_mode,
        "mornye_heal_event_mode_source": training_summary.mornye_heal_event_mode_source,
        "mechanic_event_trigger_action_ids": mechanic_event_metadata["mechanic_event_trigger_action_ids"],
        "mechanic_event_transition_trigger_action_ids": mechanic_event_metadata[
            "mechanic_event_transition_trigger_action_ids"
        ],
        "mechanic_event_emitted_counts": {},
        "fusion_burst_event_count": 0,
        "tune_rupture_shifting_event_count": 0,
        "mechanic_event_unresolved_reason": mechanic_event_metadata["mechanic_event_unresolved_reason"],
        "unsupported_aemeath_followup_mechanics": mechanic_event_metadata["unsupported_aemeath_followup_mechanics"],
        "active_echo_sets": training_summary.active_echo_sets,
        "active_weapons": training_summary.active_weapons,
        "weapon_effects_enabled": training_summary.weapon_effects_enabled,
        "weapon_effect_trigger_counts": training_summary.weapon_effect_trigger_counts,
        "weapon_effect_source_status": training_summary.weapon_effect_source_status,
        "starfield_calibrator_concerto_restore_trigger_count": (
            training_summary.starfield_calibrator_concerto_restore_trigger_count
        ),
        "starfield_calibrator_concerto_restored_total": (
            training_summary.starfield_calibrator_concerto_restored_total
        ),
        "starfield_calibrator_party_crit_damage_trigger_count": (
            training_summary.starfield_calibrator_party_crit_damage_trigger_count
        ),
        "starfield_calibrator_party_crit_damage_uptime_seconds": (
            training_summary.starfield_calibrator_party_crit_damage_uptime_seconds
        ),
        "starfield_calibrator_party_crit_damage_bonus": (
            training_summary.starfield_calibrator_party_crit_damage_bonus
        ),
        "weapon_effect_cooldown_blocked_counts": training_summary.weapon_effect_cooldown_blocked_counts,
        "discord_concerto_restore_support_status": training_summary.discord_concerto_restore_support_status,
        "echo_set_active_buffs": training_summary.echo_set_active_buffs,
        "aemeath_trailblazing_star_5set_enabled": training_summary.aemeath_trailblazing_star_5set_enabled,
        "aemeath_trailblazing_star_5set_trigger_event_tags": (
            training_summary.aemeath_trailblazing_star_5set_trigger_event_tags
        ),
        "aemeath_trailblazing_star_5set_trigger_count": training_summary.aemeath_trailblazing_star_5set_trigger_count,
        "aemeath_trailblazing_star_5set_uptime_seconds": (
            training_summary.aemeath_trailblazing_star_5set_uptime_seconds
        ),
        "aemeath_trailblazing_star_5set_buff_windows": training_summary.aemeath_trailblazing_star_5set_buff_windows,
        "high_syntony_field_active": training_summary.high_syntony_field_active,
        "high_syntony_field_remaining": training_summary.high_syntony_field_remaining,
        "high_syntony_field_created_count": training_summary.high_syntony_field_created_count,
        "high_syntony_field_def_bonus_active": training_summary.high_syntony_field_def_bonus_active,
        "high_syntony_field_def_percent_bonus": training_summary.high_syntony_field_def_percent_bonus,
        "high_syntony_field_off_tune_inherited": training_summary.high_syntony_field_off_tune_inherited,
        "high_syntony_field_heal_proxy_active": training_summary.high_syntony_field_heal_proxy_active,
        "high_syntony_field_healing_multiplier_bonus": training_summary.high_syntony_field_healing_multiplier_bonus,
        "critical_protocol_high_syntony_created_before_damage": (
            training_summary.critical_protocol_high_syntony_created_before_damage
        ),
        "high_syntony_field_same_action_application": training_summary.high_syntony_field_same_action_application,
        "high_syntony_field_application_timing": training_summary.high_syntony_field_application_timing,
        "runtime_def_percent_bonus": training_summary.runtime_def_percent_bonus,
        "current_off_tune_buildup_rate": training_summary.current_off_tune_buildup_rate,
        "enemy_off_tune_current": training_summary.enemy_off_tune_current,
        "enemy_off_tune_max": training_summary.enemy_off_tune_max,
        "enemy_mistune_active": training_summary.enemy_mistune_active,
        "enemy_tune_break_available": training_summary.enemy_tune_break_available,
        "enemy_tune_break_cooldown_seconds": training_summary.enemy_tune_break_cooldown_seconds,
        "enemy_tune_break_cooldown_source_status": training_summary.enemy_tune_break_cooldown_source_status,
        "enemy_tune_break_cooldown_source_ref": training_summary.enemy_tune_break_cooldown_source_ref,
        "enemy_tune_break_cooldown_remaining": training_summary.enemy_tune_break_cooldown_remaining,
        "off_tune_accumulation_blocked_by_tune_break_cooldown_count": (
            training_summary.off_tune_accumulation_blocked_by_tune_break_cooldown_count
        ),
        "mapped_off_tune_action_count": training_summary.mapped_off_tune_action_count,
        "unmapped_off_tune_action_ids": training_summary.unmapped_off_tune_action_ids,
        "unresolved_off_tune_damaging_action_ids": training_summary.unresolved_off_tune_damaging_action_ids,
        "off_tune_mapping_completeness_status": training_summary.off_tune_mapping_completeness_status,
        "off_tune_value_mapping_source_report": training_summary.off_tune_value_mapping_source_report,
        "tune_break_action_available_ids": training_summary.tune_break_action_available_ids,
        "tune_break_action_used_count": training_summary.tune_break_action_used_count,
        "tune_break_damage_total": training_summary.tune_break_damage_total,
        "tune_response_damage_total": training_summary.tune_response_damage_total,
        "aemeath_starburst_damage_total": training_summary.aemeath_starburst_damage_total,
        "mornye_particle_jet_damage_total": training_summary.mornye_particle_jet_damage_total,
        "aemeath_starburst_trigger_count": training_summary.aemeath_starburst_trigger_count,
        "mornye_particle_jet_trigger_count": training_summary.mornye_particle_jet_trigger_count,
        "aemeath_starburst_cooldown_blocked_count": training_summary.aemeath_starburst_cooldown_blocked_count,
        "mornye_particle_jet_cooldown_blocked_count": training_summary.mornye_particle_jet_cooldown_blocked_count,
        "tune_response_damage_formula_source_status": (
            training_summary.tune_response_damage_formula_source_status
        ),
        "tune_response_event_order_source_status": training_summary.tune_response_event_order_source_status,
        "tune_break_damage_receives_new_interfered_marker_amp": (
            training_summary.tune_break_damage_receives_new_interfered_marker_amp
        ),
        "response_damage_receives_interfered_marker_amp": (
            training_summary.response_damage_receives_interfered_marker_amp
        ),
        "response_damage_receives_newly_applied_interfered_marker_amp": (
            training_summary.response_damage_receives_newly_applied_interfered_marker_amp
        ),
        "response_damage_receives_existing_interfered_marker_amp": (
            training_summary.response_damage_receives_existing_interfered_marker_amp
        ),
        "response_damage_receives_new_interfered_marker_amp": (
            training_summary.response_damage_receives_new_interfered_marker_amp
        ),
        "target_tune_shift_state": training_summary.target_tune_shift_state,
        "target_interfered_state": training_summary.target_interfered_state,
        "interfered_marker_damage_taken_amp": training_summary.interfered_marker_damage_taken_amp,
        "unresolved_response_damage_events": training_summary.unresolved_response_damage_events,
        "halo_of_starry_radiance_5set_active": training_summary.halo_of_starry_radiance_5set_active,
        "halo_of_starry_radiance_5set_atk_percent_bonus": (
            training_summary.halo_of_starry_radiance_5set_atk_percent_bonus
        ),
        "halo_atk_buff_does_not_affect_mornye_def_damage": (
            training_summary.halo_atk_buff_does_not_affect_mornye_def_damage
        ),
        "high_syntony_field_unavailable_reason": training_summary.high_syntony_field_unavailable_reason,
        "active_build_profiles": env.get_active_build_profiles(),
        "active_party_build_profiles": env.get_active_build_profiles(),
        "effective_build_stats_summary": env.get_effective_build_stats_summary(),
        "build_profile_validation": validation,
        "stat_overrides": stat_overrides,
        "test_assumption_warning": (
            "This model was trained with test-assumption stat profiles, not verified real-game stats."
            if validation.get("warnings")
            else None
        ),
        "transition_config_source": transition_config.get("_transition_config_source", ["default"]),
        "party_preset": party_preset.get("party_id") if party_preset else None,
        "observation_shape": list(env.observation_space.shape),
        "reward": "damage_this_action / 10000.0",
        "uses_action_masks": True,
        "note": "Maskable PPO models are party-specific because action space and observation shape can change.",
    }
    results_path = PROJECT_ROOT / "results" / "training_metadata.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Saved model to {args.model_path}")
    print(f"Saved metadata to {results_path}")


def _deep_update(target: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
    return target


if __name__ == "__main__":
    main()
