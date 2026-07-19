from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or run PPO fine-tuning with periodic BC refresh stages.")
    parser.add_argument("--party", type=str, default="aemeath_mornye_lynae_enabled_test_party")
    parser.add_argument("--demo-path", type=Path, required=True)
    parser.add_argument("--initial-model", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--ppo-steps-per-cycle", type=int, default=50_000)
    parser.add_argument("--bc-epochs-per-cycle", type=int, default=3)
    parser.add_argument("--ppo-curriculum-reset-mode", type=str, default="mixed_lynae_route_curriculum")
    parser.add_argument("--ppo-ent-coef", type=float, default=0.02)
    parser.add_argument("--ppo-learning-rate", type=float, default=3e-4)
    parser.add_argument("--bc-learning-rate", type=float, default=5e-5)
    parser.add_argument("--final-none-steps", type=int, default=50_000)
    parser.add_argument("--final-ent-coef", type=float, default=0.015)
    parser.add_argument("--dry-run-plan", action="store_true")
    parser.add_argument("--no-execute", action="store_true")
    return parser


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    stages: list[dict[str, Any]] = []
    current_model = args.initial_model
    for cycle in range(1, max(0, args.cycles) + 1):
        ppo_model = Path(f"{args.output_prefix}_cycle{cycle}_ppo.zip")
        bc_model = Path(f"{args.output_prefix}_cycle{cycle}_bc_refresh.zip")
        stages.append(
            {
                "stage": f"ppo_cycle_{cycle}",
                "kind": "PPO cycle",
                "load_model": str(current_model),
                "model_path": str(ppo_model),
                "timesteps": args.ppo_steps_per_cycle,
                "curriculum_reset_mode": args.ppo_curriculum_reset_mode,
                "ent_coef": args.ppo_ent_coef,
                "learning_rate": args.ppo_learning_rate,
            }
        )
        stages.append(
            {
                "stage": f"bc_refresh_{cycle}",
                "kind": "BC refresh",
                "load_model": str(ppo_model),
                "model_path": str(bc_model),
                "epochs": args.bc_epochs_per_cycle,
                "learning_rate": args.bc_learning_rate,
                "demo_path": str(args.demo_path),
            }
        )
        current_model = bc_model
    final_model = Path(f"{args.output_prefix}_final_none.zip")
    stages.append(
        {
            "stage": "final_none_stage",
            "kind": "final none stage",
            "load_model": str(current_model),
            "model_path": str(final_model),
            "timesteps": args.final_none_steps,
            "curriculum_reset_mode": "none",
            "ent_coef": args.final_ent_coef,
            "learning_rate": args.ppo_learning_rate,
        }
    )
    return {
        "algorithm": "MaskablePPO_BC_Refresh_Plan",
        "party": args.party,
        "demo_path": str(args.demo_path),
        "initial_model": str(args.initial_model),
        "output_prefix": str(args.output_prefix),
        "cycles": args.cycles,
        "stages": stages,
        "reward_formula_unchanged": True,
        "reward_formula": "damage_this_action / 10000.0",
        "no_character_specific_usage_reward_bonus": True,
        "final_evaluation_reset_mode": "none",
        "training_only": True,
    }


def run_plan(args: argparse.Namespace) -> dict[str, Any]:
    if not args.dry_run_plan and not args.no_execute:
        from simulator.timing_training_gate import assert_timing_runtime_workload_allowed

        assert_timing_runtime_workload_allowed("PPO", ROOT)
    plan = build_plan(args)
    metadata_path = Path(f"{args.output_prefix}_plan_metadata.json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(json.dumps(plan, indent=2))
    if args.dry_run_plan or args.no_execute:
        print("bc_refresh_plan dry-run/no-execute: planned stages only; training skipped.")
        return plan
    if not args.demo_path.exists():
        raise FileNotFoundError(f"Demo path does not exist: {args.demo_path}")
    if not args.initial_model.exists():
        raise FileNotFoundError(f"Initial model does not exist: {args.initial_model}")
    for stage in plan["stages"]:
        _run_stage(stage, args.party)
    return plan


def _run_stage(stage: dict[str, Any], party: str) -> None:
    if stage["kind"] == "PPO cycle" or stage["kind"] == "final none stage":
        command = [
            sys.executable,
            str(ROOT / "rl" / "train_maskable_ppo.py"),
            "--party",
            party,
            "--load-model",
            stage["load_model"],
            "--model-path",
            stage["model_path"],
            "--timesteps",
            str(stage["timesteps"]),
            "--curriculum-reset-mode",
            stage["curriculum_reset_mode"],
            "--ent-coef",
            str(stage["ent_coef"]),
            "--learning-rate",
            str(stage["learning_rate"]),
        ]
    elif stage["kind"] == "BC refresh":
        command = [
            sys.executable,
            str(ROOT / "rl" / "pretrain_maskable_ppo_bc.py"),
            "--party",
            party,
            "--demo-path",
            stage["demo_path"],
            "--load-model",
            stage["load_model"],
            "--model-path",
            stage["model_path"],
            "--epochs",
            str(stage["epochs"]),
            "--learning-rate",
            str(stage["learning_rate"]),
        ]
    else:
        raise ValueError(f"Unsupported stage kind: {stage['kind']}")
    print("running stage command:", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    args = build_arg_parser().parse_args()
    run_plan(args)


if __name__ == "__main__":
    main()
