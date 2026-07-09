from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env.wuwa_env import WuwaDpsEnv


DEFAULT_DEMO_PATH = PROJECT_ROOT / "data" / "generated" / "route_demonstrations_aemeath_mornye_lynae.npz"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Behavior-cloning warm-start for MaskablePPO route demonstrations.")
    parser.add_argument("--party", type=str, default="aemeath_mornye_lynae_enabled_test_party")
    parser.add_argument("--demo-path", type=Path, default=DEFAULT_DEMO_PATH)
    parser.add_argument("--model-path", type=Path, default=PROJECT_ROOT / "models" / "maskable_ppo_bc_warm_start.zip")
    parser.add_argument("--load-model", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--ent-coef", type=float, default=0.0)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def load_demo(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Demo file not found: {path}")
    with np.load(path, allow_pickle=False) as data:
        metadata = json.loads(str(data["metadata_json"]))
        observations = np.asarray(data["observations"], dtype=np.float32)
        action_indices = np.asarray(data["action_indices"], dtype=np.int64)
        action_ids = np.asarray(data["action_ids"], dtype=str)
        action_masks = np.asarray(data["action_masks"], dtype=bool)
        route_ids = np.asarray(data["route_ids"], dtype=str)
        active_characters = (
            np.asarray(data["active_characters"], dtype=str)
            if "active_characters" in data
            else np.asarray([], dtype=str)
        )
    return {
        "observations": observations,
        "action_indices": action_indices,
        "action_ids": action_ids,
        "action_masks": action_masks,
        "route_ids": route_ids,
        "active_characters": active_characters,
        "metadata": metadata,
    }


def run_pretrain(args: argparse.Namespace) -> dict[str, Any]:
    demo = load_demo(args.demo_path)
    env = WuwaDpsEnv(PROJECT_ROOT / "data", party=args.party)
    observation_shape = list(env.observation_space.shape)
    action_count = int(env.action_space.n)
    _validate_demo_contract(demo, env)
    plan = {
        "demo_path": str(args.demo_path),
        "route_set_id": demo["metadata"].get("route_set_id"),
        "party": args.party,
        "sample_count": int(len(demo["action_indices"])),
        "observation_shape": observation_shape,
        "action_count": action_count,
        "action_distribution": dict(Counter(map(str, demo["action_ids"]))),
        "route_distribution": dict(Counter(map(str, demo["route_ids"]))),
        "character_distribution": dict(Counter(map(str, demo["active_characters"]))),
        "dry_run": bool(args.dry_run),
    }
    print(json.dumps(plan, indent=2))
    if args.dry_run:
        return plan

    try:
        import torch
        from sb3_contrib import MaskablePPO
    except ModuleNotFoundError as exc:
        print(f"dependency-missing: {exc}")
        raise SystemExit(3) from None

    model = _load_or_create_model(args, env, MaskablePPO)
    optimizer = model.policy.optimizer
    observations = torch.as_tensor(demo["observations"], dtype=torch.float32, device=model.device)
    action_indices = torch.as_tensor(demo["action_indices"], dtype=torch.long, device=model.device)
    action_masks = torch.as_tensor(demo["action_masks"], dtype=torch.bool, device=model.device)
    rng = np.random.default_rng(args.seed)
    losses: list[float] = []

    model.policy.train()
    for _epoch in range(max(0, args.epochs)):
        order = rng.permutation(len(action_indices))
        for start in range(0, len(order), max(1, args.batch_size)):
            batch_indices = order[start : start + max(1, args.batch_size)]
            obs_batch = observations[batch_indices]
            action_batch = action_indices[batch_indices]
            mask_batch = action_masks[batch_indices]
            distribution = model.policy.get_distribution(obs_batch, action_masks=mask_batch)
            log_prob = distribution.log_prob(action_batch)
            entropy = distribution.entropy()
            loss = -log_prob.mean()
            if args.ent_coef:
                loss = loss - float(args.ent_coef) * entropy.mean()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))

    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.model_path)
    metadata = {
        "algorithm": "MaskablePPO_BC_WarmStart",
        "demo_path": str(args.demo_path),
        "route_set_id": demo["metadata"].get("route_set_id"),
        "route_ids": sorted(set(map(str, demo["route_ids"]))),
        "route_sample_counts": dict(Counter(map(str, demo["route_ids"]))),
        "action_counts": dict(Counter(map(str, demo["action_ids"]))),
        "character_counts": dict(Counter(map(str, demo["active_characters"]))),
        "balanced_route_demo": _is_balanced_route_demo(demo),
        "party": args.party,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "ent_coef": args.ent_coef,
        "sample_count": int(len(demo["action_indices"])),
        "model_path": str(args.model_path),
        "load_model": str(args.load_model) if args.load_model else None,
        "final_loss": losses[-1] if losses else None,
        "no_character_specific_usage_reward_bonus": True,
        "reward_formula_unchanged": True,
        "reward_formula": "damage_this_action / 10000.0",
        "final_evaluation_reset_mode": "none",
        "training_only": True,
}
    sidecar = bc_metadata_path(args.model_path)
    sidecar.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return metadata


def bc_metadata_path(model_path: Path) -> Path:
    return Path(str(model_path) + ".bc_metadata.json")


def _validate_demo_contract(demo: dict[str, Any], env: WuwaDpsEnv) -> None:
    observations = demo["observations"]
    action_indices = demo["action_indices"]
    action_masks = demo["action_masks"]
    if list(observations.shape[1:]) != list(env.observation_space.shape):
        raise ValueError(
            f"Demo observation shape {list(observations.shape[1:])} does not match env {list(env.observation_space.shape)}"
        )
    if action_masks.shape != (len(action_indices), env.action_space.n):
        raise ValueError(f"Demo action mask shape {action_masks.shape} does not match env action count {env.action_space.n}")
    invalid = [
        index
        for index, action_index in enumerate(action_indices)
        if action_index < 0 or action_index >= env.action_space.n or not bool(action_masks[index, action_index])
    ]
    if invalid:
        raise ValueError(f"Demo contains invalid action indices under mask at rows: {invalid[:10]}")
    metadata_actions = demo["metadata"].get("policy_action_ids")
    if metadata_actions and list(metadata_actions) != env.get_policy_action_ids():
        raise ValueError("Demo policy_action_ids do not match env policy action space.")


def _is_balanced_route_demo(demo: dict[str, Any]) -> bool:
    route_ids = set(map(str, demo["route_ids"]))
    action_ids = set(map(str, demo["action_ids"]))
    has_non_lynae_route = any("baseline" in route_id or "aemeath_concerto_ready" in route_id for route_id in route_ids)
    has_lynae_action = any(action_id.startswith("lynae_") or action_id == "swap_to_lynae" for action_id in action_ids)
    has_non_lynae_action = any(
        not action_id.startswith("lynae_") and action_id != "swap_to_lynae"
        for action_id in action_ids
    )
    return has_non_lynae_route and has_lynae_action and has_non_lynae_action


def _load_or_create_model(args: argparse.Namespace, env: WuwaDpsEnv, maskable_ppo_class: Any) -> Any:
    if args.load_model is not None:
        if not args.load_model.exists():
            raise FileNotFoundError(f"Load model not found: {args.load_model}")
        model = maskable_ppo_class.load(
            args.load_model,
            env=env,
            learning_rate=args.learning_rate,
            ent_coef=args.ent_coef,
            device=args.device or "auto",
        )
        mismatches = _model_space_mismatches(model, env)
        if mismatches:
            raise ValueError(f"Loaded model is incompatible with demo env: {json.dumps(mismatches, indent=2)}")
        return model
    return maskable_ppo_class(
        "MlpPolicy",
        env,
        learning_rate=args.learning_rate,
        gamma=0.999,
        n_steps=512,
        batch_size=64,
        ent_coef=args.ent_coef,
        verbose=0,
        seed=args.seed,
        device=args.device or "auto",
    )


def _model_space_mismatches(model: Any, env: WuwaDpsEnv) -> dict[str, Any]:
    mismatches: dict[str, Any] = {}
    model_action_n = getattr(getattr(model, "action_space", None), "n", None)
    if model_action_n != env.action_space.n:
        mismatches["action_space_n"] = {"model": model_action_n, "env": env.action_space.n}
    model_observation_shape = list(getattr(getattr(model, "observation_space", None), "shape", []) or [])
    env_observation_shape = list(env.observation_space.shape)
    if model_observation_shape != env_observation_shape:
        mismatches["observation_shape"] = {"model": model_observation_shape, "env": env_observation_shape}
    return mismatches


def main() -> None:
    args = build_arg_parser().parse_args()
    run_pretrain(args)


if __name__ == "__main__":
    main()
