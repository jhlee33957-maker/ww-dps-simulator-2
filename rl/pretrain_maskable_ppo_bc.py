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
from simulator.timing_training_gate import assert_timing_runtime_workload_allowed
from rl.demo_contract import (
    DEFAULT_DEMO_PATH,
    DIRECT_ACTION_MANIFEST_SHA256,
    OBSERVATION_SHAPE,
    OBSERVATION_VERSION,
    POLICY_ACTION_COUNT,
    SCHEMA_VERSION,
    SOURCE_ROUTE_FILE_SHA256,
    DemoContractError,
    action_data_hash,
    array_manifest,
    file_sha256,
    json_safe,
    load_demo_npz,
    party_config_hash,
    project_relative_posix,
    validate_demo_contract,
    validate_legacy_demo_rejected,
)


DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "maskable_ppo_bc_v105.zip"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Behavior-cloning warm-start for MaskablePPO route demonstrations.")
    parser.add_argument("--party", type=str, default="aemeath_mornye_lynae_enabled_test_party")
    parser.add_argument("--initial-active-character", type=str, default=None)
    parser.add_argument("--demo-path", type=Path, default=DEFAULT_DEMO_PATH)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
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
    try:
        return load_demo_npz(path)
    except DemoContractError:
        raise
    except Exception as exc:
        raise DemoContractError(f"Could not load demo dataset {path}: {exc}") from exc


def run_pretrain(args: argparse.Namespace) -> dict[str, Any]:
    if not args.dry_run:
        assert_timing_runtime_workload_allowed("BC", PROJECT_ROOT)
    demo = load_demo(args.demo_path)
    initial_active_character = resolve_demo_initial_active_character(
        demo,
        explicit_initial_active_character=args.initial_active_character,
    )
    curriculum_reset_mode = _resolve_demo_curriculum_reset_mode(demo)
    env = WuwaDpsEnv(
        PROJECT_ROOT / "data",
        party=args.party,
        initial_active_character=initial_active_character,
        curriculum_reset_mode=curriculum_reset_mode,
    )
    env.reset(seed=args.seed)
    observation_metadata = env.observation_metadata()
    observation_shape = list(env.observation_space.shape)
    action_count = int(env.action_space.n)
    validation = _validate_demo_contract(demo, env, demo_path=args.demo_path)
    plan = {
        "demo_path": str(args.demo_path),
        "demo_sha256": file_sha256(args.demo_path),
        "demo_schema_version": demo["metadata"].get("schema_version"),
        "route_id": demo["metadata"].get("route_id"),
        "party": args.party,
        "sample_count": int(len(demo["action_indices"])),
        "observation_shape": observation_shape,
        "action_count": action_count,
        "policy_action_ids": env.get_policy_action_ids(),
        "selected_party_character_ids": env.get_selected_party_character_ids(),
        "initial_active_character": initial_active_character,
        "demo_initial_active_character": demo["metadata"].get("initial_active_character"),
        "curriculum_reset_mode": curriculum_reset_mode,
        "active_build_profiles": env.get_active_build_profiles(),
        "effective_build_stats_summary": env.get_effective_build_stats_summary(),
        "observation_metadata": observation_metadata,
        "observation_version": observation_metadata["observation_version"],
        "observation_labels": observation_metadata["observation_labels"],
        "max_party_slots": observation_metadata["max_party_slots"],
        "max_policy_action_slots": observation_metadata["max_policy_action_slots"],
        "observation_action_slot_mapping": observation_metadata["observation_action_slot_mapping"],
        "action_data_hash": demo["metadata"].get("action_data_hash"),
        "party_config_hash": demo["metadata"].get("party_config_hash"),
        "selected_sequence_sha256": demo["metadata"].get("selected_sequence_sha256"),
        "resolved_sequence_sha256": demo["metadata"].get("resolved_sequence_sha256"),
        "action_distribution": dict(Counter(map(str, demo["action_ids"]))),
        "route_distribution": dict(Counter(map(str, demo["route_ids"]))),
        "character_distribution": dict(Counter(map(str, demo["active_characters"]))),
        "contract_validation": validation,
        "array_manifest": array_manifest(demo),
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
        "demo_file_sha256": file_sha256(args.demo_path),
        "demo_schema_version": demo["metadata"].get("schema_version"),
        "source_verified_baseline_label": demo["metadata"].get("source_verified_baseline_label"),
        "demo_path": project_relative_posix(args.demo_path, root=PROJECT_ROOT),
        "route_id": demo["metadata"].get("route_id"),
        "source_route_file": demo["metadata"].get("source_route_file"),
        "source_route_file_sha256": demo["metadata"].get("source_route_file_sha256"),
        "source_route_file_sha256_expected": SOURCE_ROUTE_FILE_SHA256,
        "route_ids": sorted(set(map(str, demo["route_ids"]))),
        "route_sample_counts": dict(Counter(map(str, demo["route_ids"]))),
        "action_counts": dict(Counter(map(str, demo["action_ids"]))),
        "character_counts": dict(Counter(map(str, demo["active_characters"]))),
        "party": args.party,
        "selected_party_character_ids": env.get_selected_party_character_ids(),
        "initial_active_character": initial_active_character,
        "demo_initial_active_character": demo["metadata"].get("initial_active_character"),
        "curriculum_reset_mode": curriculum_reset_mode,
        "active_build_profiles": env.get_active_build_profiles(),
        "effective_build_stats_summary": env.get_effective_build_stats_summary(),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "ent_coef": args.ent_coef,
        "sample_count": int(len(demo["action_indices"])),
        "observation_version": demo["metadata"].get("observation_version"),
        "observation_shape": demo["metadata"].get("observation_shape"),
        "observation_labels": observation_metadata["observation_labels"],
        "max_party_slots": observation_metadata["max_party_slots"],
        "max_policy_action_slots": observation_metadata["max_policy_action_slots"],
        "observation_action_slot_mapping": observation_metadata["observation_action_slot_mapping"],
        "observation_metadata": observation_metadata,
        "policy_action_ids": demo["metadata"].get("policy_action_ids"),
        "policy_action_count": demo["metadata"].get("policy_action_count"),
        "action_data_hash": demo["metadata"].get("action_data_hash"),
        "party_config_hash": demo["metadata"].get("party_config_hash"),
        "selected_sequence_sha256": demo["metadata"].get("selected_sequence_sha256"),
        "resolved_sequence_sha256": demo["metadata"].get("resolved_sequence_sha256"),
        "baseline_total_damage": demo["metadata"].get("total_damage"),
        "baseline_dps": demo["metadata"].get("dps"),
        "bc_hyperparameters": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "ent_coef": args.ent_coef,
            "seed": args.seed,
        },
        "model_path": project_relative_posix(args.model_path, root=PROJECT_ROOT),
        "load_model": project_relative_posix(args.load_model, root=PROJECT_ROOT) if args.load_model else None,
        "final_loss": losses[-1] if losses else None,
        "no_character_specific_usage_reward_bonus": True,
        "reward_shaping": False,
        "reward_formula_unchanged": True,
        "reward_formula": "damage_this_action / 10000.0",
        "final_evaluation_reset_mode": "none",
        "training_only": True,
    }
    sidecar = bc_metadata_path(args.model_path)
    sidecar.write_text(json.dumps(json_safe(metadata), indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(json_safe(metadata), indent=2, ensure_ascii=False))
    return metadata


def bc_metadata_path(model_path: Path) -> Path:
    return Path(str(model_path) + ".bc_metadata.json")


def resolve_demo_initial_active_character(
    demo: dict[str, Any],
    *,
    explicit_initial_active_character: str | None,
) -> str:
    demo_initial = demo.get("metadata", {}).get("initial_active_character")
    if not demo_initial:
        raise DemoContractError("Demo metadata is missing initial_active_character")
    demo_initial = str(demo_initial)
    if explicit_initial_active_character:
        requested = str(explicit_initial_active_character)
        if requested != demo_initial:
            raise DemoContractError(
                "Explicit --initial-active-character "
                f"{requested!r} does not match demo metadata initial_active_character {demo_initial!r}"
            )
        return requested
    return demo_initial


def _resolve_demo_curriculum_reset_mode(demo: dict[str, Any]) -> str:
    mode = demo.get("metadata", {}).get("curriculum_reset_mode")
    if not mode:
        raise DemoContractError("Demo metadata is missing curriculum_reset_mode")
    return str(mode)


def _validate_demo_contract(demo: dict[str, Any], env: WuwaDpsEnv, *, demo_path: Path) -> dict[str, Any]:
    _reject_stale_demo_shape(demo, demo_path)
    demo_initial = str(demo["metadata"].get("initial_active_character"))
    if env.get_initial_active_character() != demo_initial:
        raise DemoContractError(
            f"Pretrainer env initial_active_character {env.get_initial_active_character()!r} "
            f"does not match demo metadata {demo_initial!r}"
        )
    demo_party_id = demo["metadata"].get("party_id")
    if demo_party_id and env.get_party_id() != demo_party_id:
        raise DemoContractError(
            f"Pretrainer env party {env.get_party_id()!r} does not match demo metadata party_id {demo_party_id!r}"
        )
    return validate_demo_contract(demo, env, root=PROJECT_ROOT)


def _reject_stale_demo_shape(demo: dict[str, Any], demo_path: Path) -> None:
    observations = np.asarray(demo.get("observations"))
    action_masks = np.asarray(demo.get("action_masks"))
    actual_shape = tuple(observations.shape[1:]) if observations.ndim >= 2 else tuple()
    actual_action_count = int(action_masks.shape[1]) if action_masks.ndim >= 2 else -1
    if actual_shape != OBSERVATION_SHAPE or actual_action_count != POLICY_ACTION_COUNT:
        result = {
            "path": demo_path.as_posix(),
            "actual_observation_shape": list(actual_shape),
            "actual_action_count": actual_action_count,
            "expected_observation_shape": list(OBSERVATION_SHAPE),
            "expected_action_count": POLICY_ACTION_COUNT,
        }
        message = (
            f"incompatible legacy BC demo {demo_path.as_posix()}: actual observation shape "
            f"{result['actual_observation_shape']} and action count {actual_action_count}; expected "
            f"observation shape {result['expected_observation_shape']} and action count {POLICY_ACTION_COUNT}"
        )
        raise DemoContractError(message)


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
