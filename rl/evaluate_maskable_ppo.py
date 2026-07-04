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
from simulator.build_profiles import parse_build_profile_overrides
from simulator.transition_config import (
    build_effective_transition_config,
    build_mornye_expectation_error_mode_override,
    build_transition_mode_overrides,
    load_transition_config,
    mechanics_mode_summary,
    transition_event_counts,
    transition_mode_summary,
)


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
    parser.add_argument("--initial-active-character", type=str, default=None)
    parser.add_argument("--transition-mode", choices=["disabled", "dry_run", "enabled"], default=None)
    parser.add_argument("--aemeath-qte-mode", choices=["disabled", "dry_run", "enabled"], default=None)
    parser.add_argument("--mornye-intro-mode", choices=["disabled", "dry_run", "enabled"], default=None)
    parser.add_argument(
        "--mornye-expectation-error-mode",
        choices=["expectation_error_only", "dry_run_success_candidate", "always_success"],
        default=None,
    )
    parser.add_argument("--allow-mismatch", action="store_true")
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
    mechanic_overrides = build_mornye_expectation_error_mode_override(args.mornye_expectation_error_mode)
    if mechanic_overrides:
        cli_overrides.update(mechanic_overrides)
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
    except ValueError as exc:
        print(f"Invalid build profile override: {exc}")
        raise SystemExit(2) from None
    model = MaskablePPO.load(args.model_path)
    env, action_sequence, resolved_action_sequence = run_masked_episode(
        model,
        PROJECT_ROOT / "data",
        deterministic=True,
        selected_character_ids=args.character_ids or args.party_character_ids,
        party=args.party,
        initial_active_character=args.initial_active_character,
        transition_config=transition_config,
        build_profile_overrides=build_profile_overrides,
    )
    metadata_path = PROJECT_ROOT / "results" / "training_metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected = {
            "selected_party_character_ids": env.get_selected_party_character_ids(),
            "policy_action_ids": env.get_policy_action_ids(),
            "observation_shape": list(env.observation_space.shape),
            "active_build_profiles": env.get_active_build_profiles(),
        }
        mismatches = {
            key: {"model": metadata.get(key), "evaluation": value}
            for key, value in expected.items()
            if metadata.get(key) != value
        }
        if mismatches and not args.allow_mismatch:
            print("Model metadata does not match the requested evaluation roster or build profile config.")
            print(json.dumps(mismatches, indent=2))
            print("Use --allow-mismatch only if you intentionally want to bypass this check.")
            raise SystemExit(1)
    summary = env.simulation.summary()
    counts = action_count_breakdown(action_sequence)
    resolved_counts = action_count_breakdown(resolved_action_sequence)
    damage_by_action: Counter[str] = Counter()
    damage_by_resolved: Counter[str] = Counter()
    damage_by_character: Counter[str] = Counter()
    damage_by_category: Counter[str] = Counter()
    damage_by_action_type: Counter[str] = Counter()
    damage_by_damage_bonus_category: Counter[str] = Counter()
    for selected_id, resolved_id, row in zip(action_sequence, resolved_action_sequence, summary.timeline):
        damage_by_action[selected_id] += row.total_action_damage
        damage_by_resolved[resolved_id] += row.total_action_damage
        damage_by_character[row.actor_character_id or row.character_id or "unknown"] += row.total_action_damage
        damage_by_category[row.damage_category] += row.total_action_damage
        damage_by_action_type[row.action_type or "other"] += row.total_action_damage
        damage_by_damage_bonus_category[row.damage_bonus_category or row.damage_category] += row.total_action_damage

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
    print("Damage by selected action:", dict(damage_by_action))
    print("Damage by resolved action:", dict(damage_by_resolved))
    print("Damage by character:", dict(damage_by_character))
    print("Damage by category:", dict(damage_by_category))
    print("Damage by action type:", dict(damage_by_action_type))
    print("Damage by damage bonus category:", dict(damage_by_damage_bonus_category))
    print("Resource summary:", summary.resources)
    print("Timeline:")
    for row in summary.timeline:
        print(row.model_dump())

    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    summary_path = results_dir / "ppo_evaluation_summary.json"
    timeline_path = results_dir / "ppo_timeline.csv"

    summary_payload = {
        "total_damage": summary.total_damage,
        "dps": summary.dps,
        "final_time": summary.final_time,
        "final_action_time": summary.final_action_time,
        "active_character": summary.active_character,
        "selected_character_ids": env.get_selected_character_ids(),
        "selected_party_character_ids": env.get_selected_party_character_ids(),
        "party_id": env.get_party_id() or args.party,
        "party_members": env.get_selected_party_character_ids(),
        "initial_active_character": env.get_initial_active_character(),
        "policy_action_ids": env.get_policy_action_ids(),
        "transition_modes": transition_mode_summary(transition_config),
        "mechanics_modes": mechanics_mode_summary(transition_config),
        "active_build_profiles": env.get_active_build_profiles(),
        "effective_build_stats_summary": env.get_effective_build_stats_summary(),
        "transition_config_source": transition_config.get("_transition_config_source", ["default"]),
        "party_preset": party_preset.get("party_id") if party_preset else None,
        **transition_event_counts(summary.timeline),
        "action_sequence": action_sequence,
        "resolved_action_sequence": resolved_action_sequence,
        "action_counts": counts,
        "resolved_action_counts": resolved_counts,
        "damage_by_selected_action": dict(damage_by_action),
        "damage_by_policy_action": dict(damage_by_action),
        "damage_by_resolved_action": dict(damage_by_resolved),
        "damage_by_character": dict(damage_by_character),
        "damage_by_category": dict(damage_by_category),
        "damage_by_action_type": dict(damage_by_action_type),
        "damage_by_damage_bonus_category": dict(damage_by_damage_bonus_category),
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
                "effective_damage_bonus": row.effective_damage_bonus,
                "build_profile_id": row.build_profile_id,
                "damage": row.total_action_damage,
            }
            for row in summary.timeline[:20]
        ],
        "resources": summary.resources,
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    timeline_rows = [row.model_dump() for row in summary.timeline]
    with timeline_path.open("w", newline="", encoding="utf-8") as file:
        if timeline_rows:
            writer = csv.DictWriter(file, fieldnames=list(timeline_rows[0]))
            writer.writeheader()
            writer.writerows(timeline_rows)

    print(f"Saved evaluation summary to {summary_path}")
    print(f"Saved timeline to {timeline_path}")


if __name__ == "__main__":
    main()
