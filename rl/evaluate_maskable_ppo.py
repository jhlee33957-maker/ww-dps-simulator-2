from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained Maskable PPO model.")
    parser.add_argument("--model-path", type=Path, default=PROJECT_ROOT / "models" / "maskable_ppo_wuwa.zip")
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
    env, action_sequence = run_masked_episode(model, PROJECT_ROOT / "data", deterministic=True)
    summary = env.simulation.summary()
    counts = action_count_breakdown(action_sequence)

    print(f"Total damage: {summary.total_damage:.2f}")
    print(f"DPS: {summary.dps:.2f}")
    print(f"Final time: {summary.final_time:.2f}")
    print("Selected action sequence:", ", ".join(action_sequence))
    print("Action count breakdown:", counts)
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
        "action_sequence": action_sequence,
        "action_counts": counts,
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
