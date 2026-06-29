from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained Maskable PPO model.")
    parser.add_argument("--model-path", type=Path, default=PROJECT_ROOT / "models" / "maskable_ppo_wuwa.zip")
    parser.add_argument("--character-ids", type=str, default=None)
    parser.add_argument("--party-character-ids", type=str, default=None)
    parser.add_argument("--party", type=str, default=None)
    parser.add_argument("--initial-active-character", type=str, default=None)
    parser.add_argument("--allow-mismatch", action="store_true")
    return parser.parse_args()


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

    model = MaskablePPO.load(args.model_path)
    env, action_sequence, resolved_action_sequence = run_masked_episode(
        model,
        PROJECT_ROOT / "data",
        deterministic=True,
        selected_character_ids=args.character_ids or args.party_character_ids or args.party,
        initial_active_character=args.initial_active_character,
    )
    metadata_path = PROJECT_ROOT / "results" / "training_metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected = {
            "selected_party_character_ids": env.get_selected_party_character_ids(),
            "policy_action_ids": env.get_policy_action_ids(),
            "observation_shape": list(env.observation_space.shape),
        }
        mismatches = {
            key: {"model": metadata.get(key), "evaluation": value}
            for key, value in expected.items()
            if metadata.get(key) != value
        }
        if mismatches and not args.allow_mismatch:
            print("Model metadata does not match the requested evaluation roster.")
            print(json.dumps(mismatches, indent=2))
            print("Use --allow-mismatch only if you intentionally want to bypass this check.")
            raise SystemExit(1)
    summary = env.simulation.summary()
    counts = action_count_breakdown(action_sequence)
    resolved_counts = action_count_breakdown(resolved_action_sequence)
    damage_by_action: Counter[str] = Counter()
    damage_by_resolved: Counter[str] = Counter()
    for selected_id, resolved_id, row in zip(action_sequence, resolved_action_sequence, summary.timeline):
        damage_by_action[selected_id] += row.total_action_damage
        damage_by_resolved[resolved_id] += row.total_action_damage

    print("Selected party:", env.get_selected_party_character_ids())
    print("Initial active character:", env.get_initial_active_character())
    print("Policy action IDs:", env.get_policy_action_ids())
    print(f"Total damage: {summary.total_damage:.2f}")
    print(f"DPS: {summary.dps:.2f}")
    print(f"Final time: {summary.final_time:.2f}")
    print("Selected action sequence:", ", ".join(action_sequence))
    print("Action count breakdown:", counts)
    print("Resolved action count breakdown:", resolved_counts)
    print("Damage by selected action:", dict(damage_by_action))
    print("Damage by resolved action:", dict(damage_by_resolved))
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
        "active_character": summary.active_character,
        "selected_character_ids": env.get_selected_character_ids(),
        "selected_party_character_ids": env.get_selected_party_character_ids(),
        "initial_active_character": env.get_initial_active_character(),
        "policy_action_ids": env.get_policy_action_ids(),
        "action_sequence": action_sequence,
        "resolved_action_sequence": resolved_action_sequence,
        "action_counts": counts,
        "resolved_action_counts": resolved_counts,
        "damage_by_selected_action": dict(damage_by_action),
        "damage_by_resolved_action": dict(damage_by_resolved),
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
