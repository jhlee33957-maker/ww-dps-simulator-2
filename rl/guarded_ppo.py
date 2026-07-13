from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = PROJECT_ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"
CANONICAL_CHECKPOINT_ROOT = PROJECT_ROOT / "models" / "guarded_ppo_v109"
CANONICAL_RESULTS_ROOT = PROJECT_ROOT / "results" / "guarded_ppo_v109"
BC_MODEL_PATH = Path("models/maskable_ppo_bc_v105.zip")
PRIOR_PPO_MODEL_PATH = Path("models/maskable_ppo_candidate_after_bc_v105.zip")
MANUAL_SUMMARY_PATH = Path("results/manual_120s_baseline_v104_summary.json")
BC_SUMMARY_PATH = Path("results/ppo_evaluation_summary.json")
PRIOR_PPO_SUMMARY_PATH = Path("results/ppo_100k_evaluation_summary.json")
BEST_TOLERANCE = 1e-6
DEFAULT_TRAINING_TIMEOUT_SECONDS = 6 * 60 * 60
DEFAULT_EVALUATION_TIMEOUT_SECONDS = 20 * 60
CPU_ENV = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}
EXPECTED_OBSERVATION_VERSION = "slot_generic_mechanics_v5"
EXPECTED_OBSERVATION_SHAPE = 314
EXPECTED_POLICY_ACTION_COUNT = 25
EXPECTED_MAX_POLICY_ACTION_SLOTS = 32
EXPECTED_ACTION_DATA_HASH = "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1"
EXPECTED_PARTY_CONFIG_HASH = "bd106ba1c0f5581436c35fea736a00fd6ad92b131f8b43ba8cf1e3dc89cbcb11"
PROJECT_RELATIVE_ANCHORS = ("data", "models", "results", "reports", "rl", "scripts")
REQUIRED_CHECKPOINT_SIDECAR_KEYS = (
    "model_path",
    "model_sha256",
    "branch_id",
    "chunk_index",
    "chunk_timesteps",
    "cumulative_branch_timesteps",
    "branch_base_seed",
    "effective_chunk_seed",
    "actual_model_seed",
    "experiment_plan_path",
    "experiment_plan_sha256",
    "source_experiment_plan_path",
    "source_experiment_plan_sha256",
    "parent_model_path",
    "parent_model_sha256",
    "selected_party_id",
    "initial_active_character",
    "curriculum_reset_mode",
    "policy_action_ids",
    "policy_action_count",
    "observation_version",
    "observation_shape",
    "max_policy_action_slots",
    "action_data_hash",
    "party_config_hash",
    "reward_formula",
    "no_character_specific_reward",
    "no_route_similarity_reward",
)


EXPECTED_BRANCHES = {
    "bc_conservative_seed_11": {
        "seed": 11,
        "mode": "model",
        "source": "models/maskable_ppo_bc_v105.zip",
        "lr": 0.0001,
        "ent": 0.005,
    },
    "bc_exploratory_seed_73": {
        "seed": 73,
        "mode": "model",
        "source": "models/maskable_ppo_bc_v105.zip",
        "lr": 0.0003,
        "ent": 0.02,
    },
    "scratch_control_seed_137": {
        "seed": 137,
        "mode": "scratch",
        "source": None,
        "lr": 0.0003,
        "ent": 0.02,
    },
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run guarded multi-branch PPO candidate v109.")
    parser.add_argument("--plan", "--plan-path", dest="plan_path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--dry-run-plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--smoke-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--only-branch", type=str, default=None)
    parser.add_argument("--max-chunks", type=int, default=None)
    parser.add_argument("--training-timeout-seconds", type=float, default=DEFAULT_TRAINING_TIMEOUT_SECONDS)
    parser.add_argument("--evaluation-timeout-seconds", type=float, default=DEFAULT_EVALUATION_TIMEOUT_SECONDS)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = parse_and_validate_guarded_ppo_args(argv)
    try:
        if args.dry_run_plan:
            result = run_dry_run_plan(args.plan_path, output_root=args.output_root)
        else:
            result = execute_plan(
                args.plan_path,
                output_root=args.output_root,
                resume=args.resume,
                only_branch=args.only_branch,
                max_chunks=args.max_chunks,
                smoke_run=args.smoke_run,
                training_timeout_seconds=args.training_timeout_seconds,
                evaluation_timeout_seconds=args.evaluation_timeout_seconds,
            )
    except ValueError as exc:
        parser = build_arg_parser()
        parser.error(str(exc))
    print(json.dumps(json_safe(result), indent=2, ensure_ascii=False))


def parse_and_validate_guarded_ppo_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    _validate_cli(args, parser)
    return args


def _validate_cli(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.resume and not args.execute:
        parser.error("--resume requires --execute")
    if not (args.dry_run_plan or args.execute or args.smoke_run):
        parser.error("No mode selected. Use --dry-run-plan, --execute, or --smoke-run.")
    if args.dry_run_plan and (args.execute or args.smoke_run):
        parser.error("--dry-run-plan cannot be combined with --execute or --smoke-run")
    if args.max_chunks is not None and args.max_chunks <= 0:
        parser.error("--max-chunks must be positive")
    if args.training_timeout_seconds <= 0:
        parser.error("--training-timeout-seconds must be positive")
    if args.evaluation_timeout_seconds <= 0:
        parser.error("--evaluation-timeout-seconds must be positive")
    if args.smoke_run:
        output_root = (args.output_root or Path(tempfile.gettempdir()) / "guarded-ppo-smoke-cli").resolve()
        if output_root == PROJECT_ROOT.resolve():
            parser.error("--smoke-run cannot target the canonical project root")
    if args.only_branch:
        plan = load_plan(args.plan_path)
        branch_ids = {str(branch.get("branch_id")) for branch in plan.get("branches", []) if isinstance(branch, dict)}
        if args.only_branch not in branch_ids:
            parser.error(f"Unknown branch for --only-branch: {args.only_branch}")


def load_plan(plan_path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    return json.loads(plan_path.read_text(encoding="utf-8"))


def validate_plan(plan: dict[str, Any], *, plan_path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    errors: list[str] = []
    branch_ids = [branch.get("branch_id") for branch in plan.get("branches", []) if isinstance(branch, dict)]
    expected_ids = list(EXPECTED_BRANCHES)
    if plan.get("schema_version") != "guarded_ppo_experiment_plan_v109":
        errors.append("schema_version must be guarded_ppo_experiment_plan_v109")
    _expect(plan, "objective", "deterministic_120s_total_damage_only", errors)
    _expect(plan, "party", "aemeath_mornye_lynae_enabled_test_party", errors)
    _expect(plan, "initial_active_character", "aemeath", errors)
    _expect(plan, "curriculum_reset_mode", "none", errors)
    _expect(plan, "deterministic_evaluation", True, errors)
    _expect(plan, "evaluation_after_every_chunk", True, errors)
    _expect(plan, "evaluation_interval_timesteps", 10000, errors)
    _expect(plan, "checkpoint_root", "models/guarded_ppo_v109", errors)
    _expect(plan, "results_root", "results/guarded_ppo_v109", errors)
    for key in (
        "global_optimum_claimed",
        "route_similarity_objective",
        "character_specific_reward",
        "bc_refresh_enabled",
        "early_stopping_enabled",
        "rollback_enabled",
        "best_checkpoint_copy_enabled",
    ):
        _expect(plan, key, False, errors)
    _expect(plan, "branch_independence", True, errors)
    if branch_ids != expected_ids:
        errors.append(f"branch order/ids mismatch: {branch_ids!r}")
    for branch in plan.get("branches", []):
        branch_id = branch.get("branch_id")
        expected = EXPECTED_BRANCHES.get(branch_id)
        if not expected:
            continue
        init = branch.get("initialization") or {}
        checks = {
            "seed": expected["seed"],
            "total_timesteps": 100000,
            "chunk_timesteps": 10000,
            "learning_rate": expected["lr"],
            "ent_coef": expected["ent"],
            "n_steps": 512,
            "batch_size": 64,
            "gamma": 0.999,
            "initial_active_character": "aemeath",
            "curriculum_reset_mode": "none",
            "continuation_mode": "continue_from_latest_branch_checkpoint",
        }
        for key, value in checks.items():
            _expect(branch, key, value, errors, prefix=f"{branch_id}.")
        _expect(init, "mode", expected["mode"], errors, prefix=f"{branch_id}.initialization.")
        _expect(init, "source_model_path", expected["source"], errors, prefix=f"{branch_id}.initialization.")
        if expected["source"]:
            source_path = PROJECT_ROOT / str(expected["source"])
            _expect(init, "source_model_sha256", sha256_file(source_path), errors, prefix=f"{branch_id}.initialization.")
    _validate_incumbents(plan, errors)
    if errors:
        raise ValueError("Guarded PPO plan contract failed:\n- " + "\n- ".join(errors))
    return {
        "status": "ok",
        "plan_path": project_relative(plan_path),
        "plan_sha256": sha256_file(plan_path),
        "branch_ids": branch_ids,
    }


def _expect(container: dict[str, Any], key: str, expected: Any, errors: list[str], *, prefix: str = "") -> None:
    actual = container.get(key)
    if actual != expected:
        errors.append(f"{prefix}{key} mismatch: actual {actual!r}, expected {expected!r}")


def _validate_incumbents(plan: dict[str, Any], errors: list[str]) -> None:
    incumbents = plan.get("incumbents") or {}
    expected = {
        "manual_baseline": (MANUAL_SUMMARY_PATH, None),
        "bc_model": (BC_SUMMARY_PATH, BC_MODEL_PATH),
        "regressed_ppo_100k": (PRIOR_PPO_SUMMARY_PATH, PRIOR_PPO_MODEL_PATH),
    }
    for incumbent_id, (summary_path, model_path) in expected.items():
        data = incumbents.get(incumbent_id) or {}
        if data.get("summary_path") != summary_path.as_posix():
            errors.append(f"incumbent {incumbent_id} summary_path mismatch")
        if model_path is None:
            continue
        if data.get("model_path") != model_path.as_posix():
            errors.append(f"incumbent {incumbent_id} model_path mismatch")
        elif data.get("model_sha256") != sha256_file(PROJECT_ROOT / model_path):
            errors.append(f"incumbent {incumbent_id} model hash mismatch")
    for path in (MANUAL_SUMMARY_PATH, BC_SUMMARY_PATH, PRIOR_PPO_SUMMARY_PATH):
        full = PROJECT_ROOT / path
        if not full.exists():
            errors.append(f"incumbent summary missing: {path.as_posix()}")
        else:
            json.loads(full.read_text(encoding="utf-8"))


def run_dry_run_plan(plan_path: Path = DEFAULT_PLAN_PATH, *, output_root: Path | None = None) -> dict[str, Any]:
    plan_path = plan_path.resolve()
    plan = load_plan(plan_path)
    validation = validate_plan(plan, plan_path=plan_path)
    root = (output_root or PROJECT_ROOT).resolve()
    commands = build_future_commands(plan, plan_path=plan_path, output_root=root)
    return {
        **validation,
        "status": "dry_run_plan_ok",
        "incumbent_records": build_incumbent_records(plan, output_root=root),
        "canonical_models_created": False,
        "canonical_results_created": False,
        "future_commands": commands,
    }


def execute_plan(
    plan_path: Path = DEFAULT_PLAN_PATH,
    *,
    output_root: Path | None = None,
    resume: bool = False,
    only_branch: str | None = None,
    max_chunks: int | None = None,
    smoke_run: bool = False,
    training_timeout_seconds: float = DEFAULT_TRAINING_TIMEOUT_SECONDS,
    evaluation_timeout_seconds: float = DEFAULT_EVALUATION_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    plan_path = plan_path.resolve()
    plan = load_plan(plan_path)
    validate_plan(plan, plan_path=plan_path)
    if only_branch and only_branch not in EXPECTED_BRANCHES:
        raise ValueError(f"Unknown branch for --only-branch: {only_branch}")
    if max_chunks is not None and max_chunks <= 0:
        raise ValueError("--max-chunks must be positive")
    if smoke_run:
        if output_root is None:
            output_root = Path(tempfile.mkdtemp(prefix="guarded-ppo-smoke-"))
        if output_root.resolve() == PROJECT_ROOT.resolve():
            raise ValueError("--smoke-run cannot target canonical output paths")
        plan = smoke_plan(plan)
    root = (output_root or PROJECT_ROOT).resolve()
    checkpoint_root = root / plan["checkpoint_root"]
    results_root = root / plan["results_root"]
    state_path = results_root / "experiment_state.json"
    if state_path.exists():
        if not resume:
            raise ValueError(f"Refusing to modify existing guarded PPO output without --resume: {state_path}")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        verify_resume_state(state, plan_path=plan_path, plan=plan, output_root=root, state_path=state_path, results_root=results_root)
    else:
        if resume:
            raise ValueError(f"--resume requested but no valid state exists at {state_path}")
        _refuse_nonempty_without_state(checkpoint_root, results_root)
        state = create_initial_state(plan, plan_path=plan_path, output_root=root, smoke_run=smoke_run)
        write_json_atomic(state_path, state)
        write_auxiliary_manifests(results_root, state)
    ensure_step_zero_records(
        plan,
        state=state,
        output_root=root,
        state_path=state_path,
        evaluation_timeout_seconds=evaluation_timeout_seconds,
    )
    write_auxiliary_manifests(results_root, state)
    completed: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for branch in plan["branches"]:
        branch_id = branch["branch_id"]
        if only_branch and branch_id != only_branch:
            continue
        branch_state = state["branches"].setdefault(branch_id, {"chunks": []})
        chunk_count = int(branch["total_timesteps"]) // int(branch["chunk_timesteps"])
        if max_chunks is not None:
            chunk_count = min(chunk_count, max_chunks)
        for chunk_index in range(1, chunk_count + 1):
            try:
                record = run_or_resume_chunk(
                    state=state,
                    branch_state=branch_state,
                    branch=branch,
                    chunk_index=chunk_index,
                    plan=plan,
                    plan_path=plan_path,
                    checkpoint_root=checkpoint_root,
                    results_root=results_root,
                    state_path=state_path,
                    output_root=root,
                    smoke_run=smoke_run,
                    training_timeout_seconds=training_timeout_seconds,
                    evaluation_timeout_seconds=evaluation_timeout_seconds,
                )
                if record and record.get("status") == "completed":
                    completed.append(record)
            except Exception as exc:
                failure = find_chunk(branch_state, chunk_index) or {
                    "branch_id": branch_id,
                    "chunk_index": chunk_index,
                }
                if failure not in branch_state.get("chunks", []):
                    branch_state.setdefault("chunks", []).append(failure)
                failure.update({"status": "failed", "error": str(exc), "failed_at": utc_timestamp()})
                write_json_atomic(state_path, state)
                failures.append(failure)
                raise
    write_auxiliary_manifests(results_root, state)
    result = {
        "status": "smoke_run_ok" if smoke_run else "guarded_ppo_run_ok",
        "output_root": root,
        "state_path": state_path,
        "completed_chunks": completed,
        "failures": failures,
        "global_best": state.get("global_best"),
    }
    if smoke_run:
        result["canonical_outputs_mutated"] = False
    return result


def create_initial_state(
    plan: dict[str, Any],
    *,
    plan_path: Path,
    output_root: Path,
    smoke_run: bool,
) -> dict[str, Any]:
    incumbents = build_incumbent_records(plan, output_root=output_root)
    state = {
        "schema_version": "guarded_ppo_experiment_state_v109",
        "plan_path": project_relative(plan_path),
        "plan_sha256": sha256_file(plan_path),
        "created_at": utc_timestamp(),
        "smoke_run": smoke_run,
        "incumbents": incumbents,
        "branches": {},
        "global_best": None,
    }
    state["global_best"] = build_best_manifest(select_best_candidate(all_records(state)), reason="initial incumbent selection")
    return state


def create_step_zero_records(plan: dict[str, Any], *, state: dict[str, Any], output_root: Path) -> None:
    ensure_step_zero_records(
        plan,
        state=state,
        output_root=output_root,
        state_path=None,
        evaluation_timeout_seconds=DEFAULT_EVALUATION_TIMEOUT_SECONDS,
    )


def ensure_step_zero_records(
    plan: dict[str, Any],
    *,
    state: dict[str, Any],
    output_root: Path,
    state_path: Path | None,
    evaluation_timeout_seconds: float,
) -> None:
    results_root = output_root / plan["results_root"]
    alias_summary_path = results_root / "step_000000000_verified_bc_alias_summary.json"
    alias_timeline_path = results_root / "step_000000000_verified_bc_alias_timeline.csv"
    alias_logs = results_root / "logs" / "step_000000000_verified_bc_alias"
    source_model_path: Path | None = None
    for branch in plan["branches"]:
        init = branch.get("initialization") or {}
        if init.get("mode") == "model":
            source_model_path = PROJECT_ROOT / init["source_model_path"]
            break
    if source_model_path is None:
        return
    staged_records: list[dict[str, Any]] = []
    for branch in plan["branches"]:
        init = branch.get("initialization") or {}
        if init.get("mode") != "model":
            continue
        branch_id = branch["branch_id"]
        branch_state = state["branches"].setdefault(branch_id, {"chunks": []})
        record = find_chunk(branch_state, 0)
        if record is None:
            record = {
                "kind": "guarded_ppo_step0_verified_bc_alias",
                "branch_id": branch_id,
                "chunk_index": 0,
                "status": "planned",
                "source_status": "verified_canonical_alias_pending_evaluation",
                "checkpoint_path": init["source_model_path"],
                "checkpoint_sha256": sha256_file(source_model_path),
                "model_sha256": sha256_file(source_model_path),
                "step0_alias_summary_path": path_for_state(alias_summary_path, output_root=output_root),
                "step0_alias_timeline_path": path_for_state(alias_timeline_path, output_root=output_root),
            }
            branch_state.setdefault("chunks", []).append(record)
        if record.get("status") != "completed":
            staged_records.append(record)
    if staged_records and state_path is not None:
        write_json_atomic(state_path, state)
    if staged_records and (not alias_summary_path.exists() or not alias_timeline_path.exists()):
        for path in (alias_summary_path, alias_timeline_path):
            if path.exists() and path.stat().st_size == 0:
                raise ValueError(f"Ambiguous empty step-0 alias output exists: {path}")
        log_result = run_command(
            build_eval_command(plan, model_path=source_model_path, summary_path=alias_summary_path, timeline_path=alias_timeline_path),
            log_dir=alias_logs,
            stage_label="step0_eval",
            timeout_seconds=evaluation_timeout_seconds,
        )
    else:
        log_result = None
    if not alias_summary_path.exists() or not alias_timeline_path.exists():
        raise ValueError("Step-0 alias evaluation is incomplete and cannot be resumed")
    summary = json.loads(alias_summary_path.read_text(encoding="utf-8"))
    for index, branch in enumerate(plan["branches"]):
        init = branch.get("initialization") or {}
        if init.get("mode") != "model":
            continue
        branch_id = branch["branch_id"]
        branch_state = state["branches"].setdefault(branch_id, {"chunks": []})
        record = find_chunk(branch_state, 0)
        if record is None:
            raise ValueError(f"Step-0 record missing after staging: {branch_id}")
        record = record_from_summary(
            summary,
            kind="guarded_ppo_step0_verified_bc_alias",
            branch_id=branch_id,
            chunk_index=0,
            cumulative_timesteps=0,
            checkpoint_path=Path(init["source_model_path"]),
            summary_path=Path(path_for_state(alias_summary_path, output_root=output_root)),
            timeline_path=Path(path_for_state(alias_timeline_path, output_root=output_root)),
            externally_verified=True,
            immutable_model=True,
            declared_order=10 + index,
        )
        record.update(
            {
                "status": "completed",
                "source_status": "verified_canonical_alias",
                "checkpoint_sha256": sha256_file(source_model_path),
                "model_sha256": sha256_file(source_model_path),
                "summary_sha256": sha256_file(alias_summary_path),
                "timeline_sha256": sha256_file(alias_timeline_path),
                "step0_shared_evaluation": True,
                "step0_alias_summary_path": path_for_state(alias_summary_path, output_root=output_root),
                "step0_alias_timeline_path": path_for_state(alias_timeline_path, output_root=output_root),
            }
        )
        if log_result:
            record.update(prefix_log_result(log_result, "evaluation", output_root=output_root))
        existing = find_chunk(branch_state, 0)
        if existing is None:
            branch_state.setdefault("chunks", []).append(record)
        else:
            existing.clear()
            existing.update(record)
    state["global_best"] = build_best_manifest(select_best_candidate(all_records(state)), reason="initial incumbent selection")
    if state_path is not None:
        write_json_atomic(state_path, state)


def build_incumbent_records(plan: dict[str, Any], *, output_root: Path) -> list[dict[str, Any]]:
    incumbent_plan = plan.get("incumbents") or {}
    records: list[dict[str, Any]] = []
    specs = [
        ("manual_baseline", "manual_baseline", None, False, 0),
        ("bc_model", "verified_bc_model", BC_MODEL_PATH, True, 1),
        ("regressed_ppo_100k", "prior_regressed_ppo_model", PRIOR_PPO_MODEL_PATH, False, 2),
    ]
    for incumbent_id, kind, model_path, verified, order in specs:
        item = incumbent_plan[incumbent_id]
        summary_rel = Path(item["summary_path"])
        summary = json.loads((PROJECT_ROOT / summary_rel).read_text(encoding="utf-8"))
        model_rel = Path(item["model_path"]) if item.get("model_path") else None
        record = record_from_summary(
            summary,
            kind=kind,
            branch_id=None,
            chunk_index=0,
            cumulative_timesteps=0,
            checkpoint_path=model_rel,
            summary_path=summary_rel,
            timeline_path=Path("results/ppo_timeline.csv") if incumbent_id == "bc_model" else None,
            externally_verified=verified,
            immutable_model=True,
            declared_order=order,
        )
        if model_rel:
            record["model_sha256"] = sha256_file(PROJECT_ROOT / model_rel)
            record["checkpoint_sha256"] = record["model_sha256"]
        else:
            record["model_sha256"] = None
            record["checkpoint_sha256"] = None
        record["incumbent_id"] = incumbent_id
        records.append(record)
    return records


def run_or_resume_chunk(
    *,
    state: dict[str, Any],
    branch_state: dict[str, Any],
    branch: dict[str, Any],
    chunk_index: int,
    plan: dict[str, Any],
    plan_path: Path,
    checkpoint_root: Path,
    results_root: Path,
    state_path: Path,
    output_root: Path,
    smoke_run: bool,
    training_timeout_seconds: float,
    evaluation_timeout_seconds: float,
) -> dict[str, Any] | None:
    existing = find_chunk(branch_state, chunk_index)
    if existing and existing.get("status") == "completed":
        return None
    branch_id = branch["branch_id"]
    model_path = checkpoint_path(checkpoint_root, branch_id, chunk_index, branch["chunk_timesteps"])
    metadata_path = Path(str(model_path) + ".ppo_metadata.json")
    branch_results = results_root / "branches" / branch_id
    summary_path = branch_results / f"step_{chunk_index * int(branch['chunk_timesteps']):09d}_summary.json"
    timeline_path = branch_results / f"step_{chunk_index * int(branch['chunk_timesteps']):09d}_timeline.csv"
    record = existing or {
        "branch_id": branch_id,
        "chunk_index": chunk_index,
        "status": "planned",
        "planned_at": utc_timestamp(),
    }
    if existing is None:
        branch_state.setdefault("chunks", []).append(record)
    parent = latest_branch_parent(branch_state, branch)
    if record.get("status") not in {"checkpoint_saved", "evaluation_started"}:
        if _checkpoint_artifacts_exist(model_path, metadata_path):
            adopted = validate_checkpoint_sidecar(
                branch=branch,
                chunk_index=chunk_index,
                plan_path=plan_path,
                model_path=model_path,
                metadata_path=metadata_path,
                parent_model_path=parent,
            )
            record.update(
                {
                    "status": "checkpoint_saved",
                    "checkpoint_saved_at": utc_timestamp(),
                    "checkpoint_adopted_from_orphan": True,
                    "checkpoint_path": path_for_state(model_path, output_root=output_root),
                    "checkpoint_sha256": adopted["model_sha256"],
                    "model_sha256": adopted["model_sha256"],
                    "metadata_path": path_for_state(metadata_path, output_root=output_root),
                    "metadata_sha256": sha256_file(metadata_path),
                    "actual_model_seed": adopted.get("actual_model_seed"),
                    "branch_base_seed": adopted.get("branch_base_seed"),
                    "effective_chunk_seed": adopted.get("effective_chunk_seed"),
                    "parent_model_path": project_relative(parent, root=PROJECT_ROOT),
                    "parent_model_sha256": sha256_file(parent) if parent else None,
                }
            )
            write_json_atomic(state_path, state)
        elif model_path.exists() or metadata_path.exists():
            raise ValueError(f"Ambiguous/corrupt orphan checkpoint artifacts for {branch_id} chunk {chunk_index}")
    if record.get("status") not in {"checkpoint_saved", "evaluation_started"}:
        record.update(
            {
                "status": "training_started",
                "training_started_at": utc_timestamp(),
                "parent_model_path": project_relative(parent, root=PROJECT_ROOT),
                "parent_model_sha256": sha256_file(parent) if parent else None,
            }
        )
        write_json_atomic(state_path, state)
        train_command = build_train_command(
            plan,
            branch,
            chunk_index=chunk_index,
            parent_model_path=parent,
            model_path=model_path,
            metadata_path=metadata_path,
            plan_path=plan_path,
            smoke_run=smoke_run,
        )
        log_result = run_command(
            train_command,
            log_dir=results_root / "logs" / branch_id / f"chunk_{chunk_index:03d}_train",
            stage_label="train",
            timeout_seconds=training_timeout_seconds,
        )
        sidecar = json.loads(metadata_path.read_text(encoding="utf-8"))
        validate_checkpoint_sidecar(
            branch=branch,
            chunk_index=chunk_index,
            plan_path=plan_path,
            model_path=model_path,
            metadata_path=metadata_path,
            parent_model_path=parent,
        )
        record.update(
            {
                "status": "checkpoint_saved",
                "checkpoint_saved_at": utc_timestamp(),
                "checkpoint_path": path_for_state(model_path, output_root=output_root),
                "checkpoint_sha256": sha256_file(model_path),
                "model_sha256": sha256_file(model_path),
                "metadata_path": path_for_state(metadata_path, output_root=output_root),
                "metadata_sha256": sha256_file(metadata_path),
                "actual_model_seed": sidecar.get("actual_model_seed"),
                "branch_base_seed": sidecar.get("branch_base_seed"),
                "effective_chunk_seed": sidecar.get("effective_chunk_seed"),
            }
        )
        record.update(prefix_log_result(log_result, "training", output_root=output_root))
        write_json_atomic(state_path, state)
    record.update({"status": "evaluation_started", "evaluation_started_at": utc_timestamp()})
    write_json_atomic(state_path, state)
    eval_command = build_eval_command(plan, model_path=model_path, summary_path=summary_path, timeline_path=timeline_path)
    try:
        eval_logs = run_command(
            eval_command,
            log_dir=results_root / "logs" / branch_id / f"chunk_{chunk_index:03d}_eval",
            stage_label="eval",
            timeout_seconds=evaluation_timeout_seconds,
        )
    except Exception:
        record.update({"status": "failed", "failure_stage": "evaluation", "failed_at": utc_timestamp()})
        write_json_atomic(state_path, state)
        raise
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    completed = record_from_summary(
        summary,
        kind="guarded_ppo_checkpoint",
        branch_id=branch_id,
        chunk_index=chunk_index,
        cumulative_timesteps=chunk_index * int(branch["chunk_timesteps"]),
        checkpoint_path=Path(record["checkpoint_path"]),
        summary_path=Path(path_for_state(summary_path, output_root=output_root)),
        timeline_path=Path(path_for_state(timeline_path, output_root=output_root)),
        externally_verified=False,
        immutable_model=True,
        declared_order=100 + len(all_records(state)),
    )
    completed.update(
        {
            "status": "completed",
            "checkpoint_sha256": record["checkpoint_sha256"],
            "model_sha256": record["checkpoint_sha256"],
            "metadata_path": record["metadata_path"],
            "metadata_sha256": record["metadata_sha256"],
            "summary_sha256": sha256_file(summary_path),
            "timeline_sha256": sha256_file(timeline_path),
            "actual_model_seed": record["actual_model_seed"],
            "branch_base_seed": record["branch_base_seed"],
            "effective_chunk_seed": record["effective_chunk_seed"],
            "completed_at": utc_timestamp(),
        }
    )
    completed.update(prefix_log_result(eval_logs, "evaluation", output_root=output_root))
    for key in ("training_stdout_log_path", "training_stdout_log_sha256", "training_stderr_log_path", "training_stderr_log_sha256"):
        if key in record:
            completed[key] = record[key]
    if record.get("checkpoint_adopted_from_orphan"):
        completed["checkpoint_adopted_from_orphan"] = True
    record.clear()
    record.update(completed)
    state["global_best"] = build_best_manifest(select_best_candidate(all_records(state)), reason="damage comparison after chunk evaluation")
    write_json_atomic(state_path, state)
    write_auxiliary_manifests(results_root, state)
    return record


def record_from_summary(
    summary: dict[str, Any],
    *,
    kind: str,
    branch_id: str | None,
    chunk_index: int,
    cumulative_timesteps: int,
    checkpoint_path: Path | None,
    summary_path: Path,
    timeline_path: Path | None,
    externally_verified: bool,
    immutable_model: bool,
    declared_order: int,
) -> dict[str, Any]:
    manual_total = float(summary.get("manual_baseline_total_damage", 5165134.682363356))
    total = float(summary["total_damage"])
    selected_hash = summary.get("selected_sequence_sha256")
    resolved_hash = summary.get("resolved_sequence_sha256")
    diagnostics = route_sequence_diagnostics(summary)
    return {
        "kind": kind,
        "winner_kind": kind,
        "branch_id": branch_id,
        "chunk_index": chunk_index,
        "cumulative_timesteps": cumulative_timesteps,
        "model_path": checkpoint_path.as_posix() if checkpoint_path else None,
        "checkpoint_path": checkpoint_path.as_posix() if checkpoint_path else None,
        "model_sha256": sha256_file(path_from_state(checkpoint_path.as_posix())) if checkpoint_path and path_from_state(checkpoint_path.as_posix()).exists() else None,
        "externally_verified": externally_verified,
        "immutable_model": immutable_model,
        "total_damage": total,
        "dps": float(summary.get("dps", total / 120.0)),
        "summary_path": summary_path.as_posix(),
        "timeline_path": timeline_path.as_posix() if timeline_path else None,
        "selected_sequence_sha256": selected_hash,
        "resolved_sequence_sha256": resolved_hash,
        "selected_action_count": summary.get("selected_action_count"),
        "resolved_action_count": summary.get("resolved_action_count"),
        "damage_by_character": summary.get("damage_by_character"),
        "scheduled_damage": (summary.get("effective_damage_role_breakdown") or {}).get("scheduled_damage"),
        "manual_baseline_damage_ratio": summary.get("manual_baseline_damage_ratio", total / manual_total),
        "manual_baseline_damage_delta": summary.get("manual_baseline_damage_delta", total - manual_total),
        "bc_damage_ratio": total / 5165134.682363356,
        "bc_damage_delta": total - 5165134.682363356,
        "selected_sequence_exact_match": diagnostics["selected_exact_match"],
        "resolved_sequence_exact_match": diagnostics["resolved_exact_match"],
        "selected_sequence_agreement_count": diagnostics["selected_agreement_count"],
        "selected_sequence_agreement_ratio": diagnostics["selected_agreement_ratio"],
        "resolved_sequence_agreement_count": diagnostics["resolved_agreement_count"],
        "resolved_sequence_agreement_ratio": diagnostics["resolved_agreement_ratio"],
        "selected_sequence_common_prefix_length": diagnostics["selected_common_prefix_length"],
        "selected_sequence_common_prefix_ratio": diagnostics["selected_common_prefix_ratio"],
        "resolved_sequence_common_prefix_length": diagnostics["resolved_common_prefix_length"],
        "resolved_sequence_common_prefix_ratio": diagnostics["resolved_common_prefix_ratio"],
        "first_selected_action_divergence": diagnostics["first_selected_divergence"],
        "first_resolved_action_divergence": diagnostics["first_resolved_divergence"],
        "route_agreement_ratio_diagnostic_only": diagnostics["route_agreement_ratio"],
        "model_training_metadata_source": summary.get("model_training_metadata_source"),
        "model_training_metadata_path": normalize_summary_metadata_path(summary.get("model_training_metadata_path")),
        "model_metadata_mismatches": summary.get("model_metadata_mismatches"),
        "model_space_mismatches": summary.get("model_space_mismatches"),
        "final_combat_time": summary.get("final_time"),
        "declared_order": declared_order,
    }


def route_sequence_diagnostics(summary: dict[str, Any]) -> dict[str, Any]:
    baseline = json.loads((PROJECT_ROOT / MANUAL_SUMMARY_PATH).read_text(encoding="utf-8"))
    baseline_selected = baseline.get("selected_action_sequence") or baseline.get("action_sequence") or []
    baseline_resolved = baseline.get("resolved_action_sequence") or []
    selected = summary.get("action_sequence") or summary.get("selected_action_sequence") or []
    resolved = summary.get("resolved_action_sequence") or []
    selected_diag = compare_sequences(baseline_selected, selected)
    resolved_diag = compare_sequences(baseline_resolved, resolved)
    ratios = [value for value in (selected_diag["agreement_ratio"], resolved_diag["agreement_ratio"]) if value is not None]
    route_ratio = sum(ratios) / len(ratios) if ratios else None
    return {
        "selected_exact_match": selected_diag["exact_match"],
        "resolved_exact_match": resolved_diag["exact_match"],
        "selected_agreement_count": selected_diag["agreement_count"],
        "selected_agreement_ratio": selected_diag["agreement_ratio"],
        "resolved_agreement_count": resolved_diag["agreement_count"],
        "resolved_agreement_ratio": resolved_diag["agreement_ratio"],
        "selected_common_prefix_length": selected_diag["common_prefix_length"],
        "selected_common_prefix_ratio": selected_diag["common_prefix_ratio"],
        "resolved_common_prefix_length": resolved_diag["common_prefix_length"],
        "resolved_common_prefix_ratio": resolved_diag["common_prefix_ratio"],
        "first_selected_divergence": selected_diag["first_divergence"],
        "first_resolved_divergence": resolved_diag["first_divergence"],
        "route_agreement_ratio": route_ratio,
    }


def compare_sequences(baseline: list[Any], candidate: list[Any]) -> dict[str, Any]:
    max_len = max(len(baseline), len(candidate))
    min_len = min(len(baseline), len(candidate))
    agreement_count = sum(1 for index in range(min_len) if baseline[index] == candidate[index])
    common_prefix = 0
    for index in range(min_len):
        if baseline[index] != candidate[index]:
            break
        common_prefix += 1
    first_divergence = None
    if baseline != candidate:
        divergence_index = common_prefix
        first_divergence = {
            "zero_based_step": divergence_index,
            "baseline": baseline[divergence_index] if divergence_index < len(baseline) else None,
            "candidate": candidate[divergence_index] if divergence_index < len(candidate) else None,
        }
    return {
        "exact_match": baseline == candidate,
        "agreement_count": agreement_count,
        "agreement_ratio": agreement_count / max_len if max_len else 1.0,
        "common_prefix_length": common_prefix,
        "common_prefix_ratio": common_prefix / max_len if max_len else 1.0,
        "first_divergence": first_divergence,
    }


def normalize_summary_metadata_path(value: Any) -> str | None:
    if not value:
        return None
    return canonicalize_guarded_path(str(value))


def canonicalize_guarded_path(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    normalized = raw.replace("\\", "/")
    path = Path(raw)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        except ValueError:
            suffix = _project_relative_suffix(normalized)
            return suffix or _sanitized_guarded_filename(path.name)
    if normalized.startswith("/"):
        suffix = _project_relative_suffix(normalized)
        return suffix or _sanitized_guarded_filename(normalized)
    windows = PureWindowsPath(raw)
    if windows.is_absolute() or windows.drive:
        suffix = _project_relative_suffix(windows.as_posix())
        return suffix or _sanitized_guarded_filename(windows.name)
    suffix = _project_relative_suffix(normalized)
    if suffix:
        return suffix
    return normalized.lstrip("./")


def _project_relative_suffix(value: str) -> str | None:
    parts = [part for part in value.replace("\\", "/").split("/") if part and part != "."]
    for index in range(len(parts) - 1, -1, -1):
        part = parts[index]
        if part in PROJECT_RELATIVE_ANCHORS:
            return "/".join(parts[index:])
    return None


def _sanitized_guarded_filename(value: str) -> str:
    name = value.replace("\\", "/").rsplit("/", 1)[-1].strip()
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in name)
    return safe or "unknown"


def smoke_plan(plan: dict[str, Any]) -> dict[str, Any]:
    plan = json.loads(json.dumps(plan))
    plan["checkpoint_root"] = "models/guarded_ppo_v109_smoke"
    plan["results_root"] = "results/guarded_ppo_v109_smoke"
    for branch in plan["branches"]:
        branch["total_timesteps"] = 32
        branch["chunk_timesteps"] = 32
        branch["n_steps"] = 32
        branch["batch_size"] = 32
    return plan


def latest_branch_parent(branch_state: dict[str, Any], branch: dict[str, Any]) -> Path | None:
    completed = [item for item in branch_state.get("chunks", []) if item.get("status") == "completed"]
    if completed:
        latest = max(completed, key=lambda item: int(item["chunk_index"]))
        return path_from_state(latest["checkpoint_path"])
    init = branch.get("initialization") or {}
    if init.get("mode") == "model":
        return PROJECT_ROOT / init["source_model_path"]
    return None


def find_chunk(branch_state: dict[str, Any], chunk_index: int) -> dict[str, Any] | None:
    for chunk in branch_state.get("chunks", []):
        if int(chunk.get("chunk_index", -1)) == int(chunk_index):
            return chunk
    return None


def _checkpoint_artifacts_exist(model_path: Path, metadata_path: Path) -> bool:
    return model_path.exists() and metadata_path.exists()


def validate_checkpoint_sidecar(
    *,
    branch: dict[str, Any],
    chunk_index: int,
    plan_path: Path,
    model_path: Path,
    metadata_path: Path,
    parent_model_path: Path | None,
) -> dict[str, Any]:
    if not model_path.exists() or not metadata_path.exists():
        raise ValueError(f"checkpoint/sidecar pair is incomplete: {model_path} / {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    expected_seed = effective_seed(branch, chunk_index)
    model_sha = sha256_file(model_path)
    expected_parent_path = canonicalize_guarded_path(project_relative(parent_model_path, root=PROJECT_ROOT)) if parent_model_path else None
    expected_parent_sha = sha256_file(parent_model_path) if parent_model_path else None
    expected_model_path = canonicalize_guarded_path(project_relative(model_path, root=PROJECT_ROOT))
    expected_plan_path = canonicalize_guarded_path(project_relative(plan_path, root=PROJECT_ROOT))
    checks = {
        "model_path": expected_model_path,
        "model_sha256": model_sha,
        "branch_id": branch["branch_id"],
        "chunk_index": chunk_index,
        "chunk_timesteps": int(branch["chunk_timesteps"]),
        "cumulative_branch_timesteps": chunk_index * int(branch["chunk_timesteps"]),
        "branch_base_seed": int(branch["seed"]),
        "effective_chunk_seed": expected_seed,
        "actual_model_seed": expected_seed,
        "experiment_plan_path": expected_plan_path,
        "experiment_plan_sha256": sha256_file(plan_path),
        "source_experiment_plan_path": expected_plan_path,
        "source_experiment_plan_sha256": sha256_file(plan_path),
        "parent_model_path": expected_parent_path,
        "parent_model_sha256": expected_parent_sha,
        "selected_party_id": "aemeath_mornye_lynae_enabled_test_party",
        "initial_active_character": branch["initial_active_character"],
        "curriculum_reset_mode": branch["curriculum_reset_mode"],
        "observation_version": EXPECTED_OBSERVATION_VERSION,
        "policy_action_count": EXPECTED_POLICY_ACTION_COUNT,
        "max_policy_action_slots": EXPECTED_MAX_POLICY_ACTION_SLOTS,
        "action_data_hash": EXPECTED_ACTION_DATA_HASH,
        "party_config_hash": EXPECTED_PARTY_CONFIG_HASH,
        "no_character_specific_reward": True,
        "no_route_similarity_reward": True,
    }
    errors: list[str] = []
    missing = [key for key in REQUIRED_CHECKPOINT_SIDECAR_KEYS if key not in metadata]
    if missing:
        errors.append(f"missing required sidecar fields: {missing}")
    for key, expected in checks.items():
        actual = metadata.get(key)
        if key in {"model_path", "experiment_plan_path", "source_experiment_plan_path", "parent_model_path"}:
            actual = canonicalize_guarded_path(actual)
        if actual != expected:
            errors.append(f"{key} {actual!r} != {expected!r}")
    shape = metadata.get("observation_shape")
    if shape not in ([EXPECTED_OBSERVATION_SHAPE], EXPECTED_OBSERVATION_SHAPE):
        errors.append(f"observation_shape {shape!r} != {EXPECTED_OBSERVATION_SHAPE}")
    if metadata.get("policy_action_ids") != expected_policy_action_ids():
        errors.append("policy_action_ids missing or order mismatch")
    reward_formula = metadata.get("reward_formula")
    if reward_formula not in {"damage_this_action / 10000.0", "damage_delta", "damage_only", "deterministic_120s_total_damage_only"}:
        errors.append(f"reward_formula unsupported/missing: {reward_formula!r}")
    if errors:
        raise ValueError("checkpoint sidecar contract failed: " + "; ".join(errors))
    return metadata


def expected_policy_action_ids() -> list[str]:
    from env.wuwa_env import WuwaDpsEnv

    env = WuwaDpsEnv(
        PROJECT_ROOT / "data",
        party="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
        curriculum_reset_mode="none",
    )
    return list(env.get_policy_action_ids())


def select_best_candidate(candidates: list[dict[str, Any]], *, tolerance: float = BEST_TOLERANCE) -> dict[str, Any] | None:
    if not candidates:
        return None
    best = candidates[0]
    for candidate in candidates[1:]:
        delta = float(candidate["total_damage"]) - float(best["total_damage"])
        if delta > tolerance:
            best = candidate
        elif abs(delta) <= tolerance and _tie_rank(candidate) > _tie_rank(best):
            best = candidate
    return dict(best)


def _tie_rank(record: dict[str, Any]) -> tuple[int, int, int]:
    verified_immutable = int(bool(record.get("externally_verified")) and bool(record.get("immutable_model")))
    earlier = -int(record.get("declared_order", 10_000_000))
    model_present = int(bool(record.get("model_path")))
    return (verified_immutable, earlier, model_present)


def build_best_manifest(record: dict[str, Any] | None, *, reason: str) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "winner_kind": record.get("winner_kind") or record.get("kind"),
        "model_path": record.get("model_path"),
        "model_sha256": record.get("model_sha256") or record.get("checkpoint_sha256"),
        "externally_verified": bool(record.get("externally_verified")),
        "branch_id": record.get("branch_id"),
        "cumulative_steps": record.get("cumulative_timesteps"),
        "total_damage": record.get("total_damage"),
        "dps": record.get("dps"),
        "evaluation_summary_path": record.get("summary_path"),
        "selected_sequence_sha256": record.get("selected_sequence_sha256"),
        "resolved_sequence_sha256": record.get("resolved_sequence_sha256"),
        "manual_baseline_damage_ratio": record.get("manual_baseline_damage_ratio"),
        "manual_baseline_damage_delta": record.get("manual_baseline_damage_delta"),
        "bc_damage_ratio": record.get("bc_damage_ratio"),
        "bc_damage_delta": record.get("bc_damage_delta"),
        "winner_selection_reason": reason,
        "global_optimum_proven": False,
    }


def build_leaderboard(state: dict[str, Any]) -> dict[str, Any]:
    records = sorted(all_records(state), key=lambda item: float(item["total_damage"]), reverse=True)
    return {
        "schema_version": "guarded_ppo_leaderboard_v109",
        "updated_at": utc_timestamp(),
        "objective": "deterministic_120s_total_damage_only",
        "selection_tolerance": BEST_TOLERANCE,
        "global_best": state.get("global_best"),
        "records": records,
    }


def all_records(state: dict[str, Any]) -> list[dict[str, Any]]:
    records = list(state.get("incumbents") or [])
    for branch_state in state.get("branches", {}).values():
        records.extend(item for item in branch_state.get("chunks", []) if item.get("status") == "completed")
    return records


def verify_resume_state(
    state: dict[str, Any],
    *,
    plan_path: Path,
    plan: dict[str, Any],
    output_root: Path | None = None,
    state_path: Path | None = None,
    results_root: Path | None = None,
) -> None:
    if state.get("plan_sha256") != sha256_file(plan_path):
        raise ValueError("Resume state plan_sha256 does not match the current plan")
    incumbent_errors: list[str] = []
    _validate_incumbents(plan, incumbent_errors)
    if incumbent_errors:
        raise ValueError("Resume incumbent verification failed:\n- " + "\n- ".join(incumbent_errors))
    plan_ids = [branch["branch_id"] for branch in plan["branches"]]
    unknown = sorted(set(state.get("branches", {})) - set(plan_ids))
    if unknown:
        raise ValueError(f"Resume state contains unknown branch ids: {unknown}")
    expected_incumbents = build_incumbent_records(plan, output_root=output_root or PROJECT_ROOT)
    _assert_incumbents_match(state.get("incumbents") or [], expected_incumbents)
    for branch_id, branch_state in state.get("branches", {}).items():
        seen_chunks: set[int] = set()
        branch = next(item for item in plan["branches"] if item["branch_id"] == branch_id)
        for record in branch_state.get("chunks", []):
            chunk_index = int(record.get("chunk_index", -1))
            if chunk_index in seen_chunks:
                raise ValueError(f"Duplicate resume record for {branch_id} chunk {chunk_index}")
            seen_chunks.add(chunk_index)
            checkpoint_value = record.get("checkpoint_path")
            if checkpoint_value:
                checkpoint = path_from_state(checkpoint_value)
                _require_hash(checkpoint, record.get("checkpoint_sha256"), "checkpoint")
                if record.get("model_sha256") and record.get("model_sha256") != record.get("checkpoint_sha256"):
                    raise ValueError(f"record model_sha256/checkpoint_sha256 mismatch: {checkpoint}")
            metadata_value = record.get("metadata_path")
            if metadata_value:
                metadata_path = path_from_state(metadata_value)
                _require_hash(metadata_path, record.get("metadata_sha256"), "sidecar")
                validate_checkpoint_sidecar(
                    branch=branch,
                    chunk_index=chunk_index,
                    plan_path=plan_path,
                    model_path=path_from_state(checkpoint_value),
                    metadata_path=metadata_path,
                    parent_model_path=_expected_parent_for_record(state, branch, chunk_index),
                )
            _verify_record_logs(record)
            if record.get("status") == "completed":
                summary = path_from_state(record["summary_path"])
                timeline = path_from_state(record["timeline_path"])
                _require_hash(summary, record.get("summary_sha256"), "summary")
                _require_hash(timeline, record.get("timeline_sha256"), "timeline")
                summary_data = json.loads(summary.read_text(encoding="utf-8"))
                if summary_data.get("model_training_metadata_source") not in {"ppo_model_sidecar", "bc_model_sidecar"}:
                    raise ValueError(f"summary metadata source missing/invalid: {summary}")
                if metadata_value and summary_data.get("model_training_metadata_source") != "ppo_model_sidecar":
                    raise ValueError(f"summary metadata source does not match PPO checkpoint: {summary}")
                if metadata_value and normalize_summary_metadata_path(summary_data.get("model_training_metadata_path")) != normalize_summary_metadata_path(metadata_value):
                    raise ValueError(f"summary metadata path does not match checkpoint sidecar: {summary}")
                if summary_data.get("selected_sequence_sha256") != record.get("selected_sequence_sha256"):
                    raise ValueError(f"summary selected hash mismatch: {summary}")
                if summary_data.get("resolved_sequence_sha256") != record.get("resolved_sequence_sha256"):
                    raise ValueError(f"summary resolved hash mismatch: {summary}")
                if abs(float(summary_data.get("final_time", -1.0)) - 120.0) > 1e-6:
                    raise ValueError(f"summary final time mismatch: {summary}")
    recomputed_best = build_best_manifest(select_best_candidate(all_records(state)), reason="damage comparison after resume verification")
    if not _best_manifest_equal(state.get("global_best"), recomputed_best):
        state["global_best"] = recomputed_best
        if state_path is not None:
            write_json_atomic(state_path, state)
        if results_root is not None:
            write_auxiliary_manifests(results_root, state)


def _require_hash(path: Path, expected: str | None, label: str) -> None:
    if not path.exists():
        raise ValueError(f"Resume {label} missing: {path}")
    if expected and sha256_file(path) != expected:
        raise ValueError(f"Resume {label} hash mismatch: {path}")


def _assert_incumbents_match(actual: list[dict[str, Any]], expected: list[dict[str, Any]]) -> None:
    if len(actual) != len(expected):
        raise ValueError("Resume incumbent count mismatch")
    keys = ("kind", "incumbent_id", "model_path", "model_sha256", "checkpoint_sha256", "summary_path", "total_damage")
    for left, right in zip(actual, expected):
        for key in keys:
            if left.get(key) != right.get(key):
                raise ValueError(f"Resume incumbent {key} mismatch: {left.get(key)!r} != {right.get(key)!r}")


def _expected_parent_for_record(state: dict[str, Any], branch: dict[str, Any], chunk_index: int) -> Path | None:
    if chunk_index <= 0:
        init = branch.get("initialization") or {}
        return PROJECT_ROOT / init["source_model_path"] if init.get("mode") == "model" else None
    if chunk_index == 1:
        init = branch.get("initialization") or {}
        return PROJECT_ROOT / init["source_model_path"] if init.get("mode") == "model" else None
    branch_state = state.get("branches", {}).get(branch["branch_id"], {})
    previous = find_chunk(branch_state, chunk_index - 1)
    if previous and previous.get("status") == "completed":
        return path_from_state(previous["checkpoint_path"])
    return None


def _verify_record_logs(record: dict[str, Any]) -> None:
    for prefix in ("training", "evaluation"):
        for stream in ("stdout", "stderr"):
            path_key = f"{prefix}_{stream}_log_path"
            sha_key = f"{prefix}_{stream}_log_sha256"
            if path_key in record:
                _require_hash(path_from_state(record[path_key]), record.get(sha_key), f"{prefix} {stream} log")


def _best_manifest_equal(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    ignored = {"winner_selection_reason"}
    left_filtered = {key: value for key, value in dict(left).items() if key not in ignored}
    right_filtered = {key: value for key, value in dict(right).items() if key not in ignored}
    return left_filtered == right_filtered


def build_future_commands(plan: dict[str, Any], *, plan_path: Path, output_root: Path) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    checkpoint_root = output_root / plan["checkpoint_root"]
    results_root = output_root / plan["results_root"]
    branch_results_root = results_root / "branches"
    step0_model: Path | None = None
    step0_aliases: list[str] = []
    for branch in plan["branches"]:
        init = branch["initialization"]
        if init["mode"] == "model":
            step0_model = PROJECT_ROOT / init["source_model_path"]
            step0_aliases.append(branch["branch_id"])
    if step0_model is not None:
        shared_summary = results_root / "step_000000000_verified_bc_alias_summary.json"
        shared_timeline = results_root / "step_000000000_verified_bc_alias_timeline.csv"
        commands.append(
            {
                "chunk_index": 0,
                "step_0_shared_evaluation": {
                    "model_path": project_relative(step0_model),
                    "model_sha256": sha256_file(step0_model),
                    "summary_path": shared_summary.as_posix(),
                    "timeline_path": shared_timeline.as_posix(),
                },
                "step_0_aliases": [
                    {
                        "branch_id": branch_id,
                        "source_status": "verified_canonical_alias",
                        "summary_path": shared_summary.as_posix(),
                        "timeline_path": shared_timeline.as_posix(),
                    }
                    for branch_id in step0_aliases
                ],
            }
        )
    for branch in plan["branches"]:
        chunk_count = int(branch["total_timesteps"]) // int(branch["chunk_timesteps"])
        parent = PROJECT_ROOT / branch["initialization"]["source_model_path"] if branch["initialization"]["mode"] == "model" else None
        for chunk_index in range(1, chunk_count + 1):
            model_path = checkpoint_path(checkpoint_root, branch["branch_id"], chunk_index, branch["chunk_timesteps"])
            summary_path = branch_results_root / branch["branch_id"] / f"step_{chunk_index * int(branch['chunk_timesteps']):09d}_summary.json"
            timeline_path = branch_results_root / branch["branch_id"] / f"step_{chunk_index * int(branch['chunk_timesteps']):09d}_timeline.csv"
            commands.append(
                {
                    "branch_id": branch["branch_id"],
                    "chunk_index": chunk_index,
                    "continuation_parent": project_relative(parent) if parent else None,
                    "effective_chunk_seed": effective_seed(branch, chunk_index),
                    "train": build_train_command(
                        plan,
                        branch,
                        chunk_index=chunk_index,
                        parent_model_path=parent,
                        model_path=model_path,
                        metadata_path=Path(str(model_path) + ".ppo_metadata.json"),
                        plan_path=plan_path,
                    ),
                    "evaluate": build_eval_command(plan, model_path=model_path, summary_path=summary_path, timeline_path=timeline_path),
                }
            )
            parent = model_path
    return commands


def build_train_command(
    plan: dict[str, Any],
    branch: dict[str, Any],
    *,
    chunk_index: int,
    parent_model_path: Path | None,
    model_path: Path,
    metadata_path: Path,
    plan_path: Path,
    smoke_run: bool = False,
) -> list[str]:
    chunk_timesteps = int(branch["chunk_timesteps"])
    seed = effective_seed(branch, chunk_index)
    command = [
        sys.executable,
        "rl/train_maskable_ppo.py",
        "--timesteps",
        str(chunk_timesteps),
        "--model-path",
        str(model_path),
        "--seed",
        str(seed),
        "--branch-base-seed",
        str(branch["seed"]),
        "--effective-chunk-seed",
        str(seed),
        "--party",
        plan["party"],
        "--initial-active-character",
        branch["initial_active_character"],
        "--curriculum-reset-mode",
        branch["curriculum_reset_mode"],
        "--learning-rate",
        str(branch["learning_rate"]),
        "--ent-coef",
        str(branch["ent_coef"]),
        "--n-steps",
        str(branch["n_steps"]),
        "--batch-size",
        str(branch["batch_size"]),
        "--gamma",
        str(branch["gamma"]),
        "--branch-id",
        branch["branch_id"],
        "--chunk-index",
        str(chunk_index),
        "--cumulative-timesteps",
        str(chunk_index * chunk_timesteps),
        "--experiment-plan-path",
        str(plan_path),
        "--metadata-path",
        str(metadata_path),
        "--progress-every-steps",
        str(chunk_timesteps),
        "--log-interval",
        "1",
        "--verbose",
        "0" if smoke_run else "1",
    ]
    if parent_model_path is not None:
        parent_sha = sha256_file(parent_model_path) if parent_model_path.exists() else "future_checkpoint_pending"
        command.extend(["--load-model", str(parent_model_path), "--parent-model-sha256", parent_sha])
    if smoke_run:
        command.append("--skip-global-metadata")
    return command


def build_eval_command(plan: dict[str, Any], *, model_path: Path, summary_path: Path, timeline_path: Path) -> list[str]:
    return [
        sys.executable,
        "rl/evaluate_maskable_ppo.py",
        "--model-path",
        str(model_path),
        "--party",
        plan["party"],
        "--initial-active-character",
        plan["initial_active_character"],
        "--summary-path",
        str(summary_path),
        "--timeline-path",
        str(timeline_path),
    ]


def effective_seed(branch: dict[str, Any], chunk_index: int) -> int:
    return int(branch["seed"]) + int(chunk_index) - 1


def checkpoint_path(root: Path, branch_id: str, chunk_index: int, chunk_timesteps: int) -> Path:
    return root / branch_id / f"step_{chunk_index * int(chunk_timesteps):09d}.zip"


def run_command(
    command: list[str],
    *,
    log_dir: Path | None = None,
    stage_label: str = "stage",
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    env = dict(os.environ)
    env.update(CPU_ENV)
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    started = time.perf_counter()
    log_dir = log_dir or (Path(tempfile.gettempdir()) / "guarded-ppo-logs" / f"{stage_label}-{int(started * 1000)}")
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / f"{stage_label}.stdout.log"
    stderr_path = log_dir / f"{stage_label}.stderr.log"
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process_kwargs: dict[str, Any] = {
        "cwd": PROJECT_ROOT,
        "env": env,
        "stdout": None,
        "stderr": None,
        "creationflags": creationflags,
        "text": False,
    }
    if os.name != "nt":
        process_kwargs["start_new_session"] = True
    with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
        process_kwargs["stdout"] = stdout_file
        process_kwargs["stderr"] = stderr_file
        process = subprocess.Popen(command, **process_kwargs)
        try:
            returncode = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            _terminate_process_tree(process)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _kill_process_tree(process)
                process.wait(timeout=10)
            elapsed = time.perf_counter() - started
            stdout_file.flush()
            stderr_file.flush()
            raise RuntimeError(
                _format_command_failure(
                    command=command,
                    elapsed=elapsed,
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    timeout_seconds=timeout_seconds,
                    timed_out=True,
                )
            ) from exc
    elapsed = time.perf_counter() - started
    if returncode != 0:
        raise RuntimeError(
            _format_command_failure(
                command=command,
                elapsed=elapsed,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                returncode=returncode,
                timeout_seconds=timeout_seconds,
            )
        )
    return {
        "elapsed_seconds": elapsed,
        "stdout_log_path": stdout_path,
        "stdout_log_sha256": sha256_file(stdout_path),
        "stderr_log_path": stderr_path,
        "stderr_log_sha256": sha256_file(stderr_path),
    }


def prefix_log_result(log_result: dict[str, Any], prefix: str, *, output_root: Path) -> dict[str, Any]:
    return {
        f"{prefix}_elapsed_seconds": log_result["elapsed_seconds"],
        f"{prefix}_stdout_log_path": path_for_state(Path(log_result["stdout_log_path"]), output_root=output_root),
        f"{prefix}_stdout_log_sha256": log_result["stdout_log_sha256"],
        f"{prefix}_stderr_log_path": path_for_state(Path(log_result["stderr_log_path"]), output_root=output_root),
        f"{prefix}_stderr_log_sha256": log_result["stderr_log_sha256"],
    }


def _format_command_failure(
    *,
    command: list[str],
    elapsed: float,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: float | None,
    returncode: int | None = None,
    timed_out: bool = False,
) -> str:
    status = "timeout" if timed_out else f"returncode: {returncode}"
    return (
        "Command failed\n"
        f"{status}\n"
        f"command: {' '.join(command)}\n"
        f"elapsed_seconds: {elapsed:.6f}\n"
        f"timeout_seconds: {timeout_seconds}\n"
        f"stdout_log: {stdout_path}\n"
        f"stderr_log: {stderr_path}\n"
        f"stdout_tail:\n{_tail_text(stdout_path)}\n"
        f"stderr_tail:\n{_tail_text(stderr_path)}"
    )


def _tail_text(path: Path, limit: int = 4000) -> str:
    data = path.read_bytes()
    return data[-limit:].decode("utf-8", errors="replace")


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        try:
            os.killpg(process.pid, 15)
        except ProcessLookupError:
            pass


def _kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        try:
            os.killpg(process.pid, 9)
        except ProcessLookupError:
            pass


def _refuse_nonempty_without_state(*roots: Path) -> None:
    for root in roots:
        if root.exists() and any(root.iterdir()):
            raise ValueError(f"Refusing non-resume execution into non-empty experiment directory without state: {root}")


def write_auxiliary_manifests(results_root: Path, state: dict[str, Any]) -> None:
    write_json_atomic(results_root / "leaderboard.json", build_leaderboard(state))
    write_json_atomic(results_root / "best_checkpoint.json", state.get("global_best"))


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(json_safe(data), indent=2, ensure_ascii=False)
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(payload, encoding="utf-8")
    temp_path.replace(path)


def write_json(path: Path, data: Any) -> None:
    write_json_atomic(path, data)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_for_state(path: Path, *, output_root: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def path_from_state(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def project_relative(path: Path | None, *, root: Path = PROJECT_ROOT) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, Path):
        return project_relative(value)
    return value


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
