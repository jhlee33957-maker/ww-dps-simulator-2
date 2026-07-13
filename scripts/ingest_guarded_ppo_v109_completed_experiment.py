from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PLAN_PATH = ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"
RESULTS_ROOT = ROOT / "results" / "guarded_ppo_v109"
STATE_PATH = RESULTS_ROOT / "experiment_state.json"
LEADERBOARD_PATH = RESULTS_ROOT / "leaderboard.json"
BEST_PATH = RESULTS_ROOT / "best_checkpoint.json"
FINAL_SUMMARY_PATH = RESULTS_ROOT / "final_experiment_summary.json"
FINAL_REPORT_PATH = ROOT / "reports" / "guarded_ppo_experiment_v109_results.md"
PRIOR_PPO_MODEL = ROOT / "models" / "maskable_ppo_candidate_after_bc_v105.zip"
PRIOR_PPO_SIDECAR = Path(str(PRIOR_PPO_MODEL) + ".ppo_metadata.json")
PRIOR_PPO_SUMMARY = ROOT / "results" / "ppo_100k_evaluation_summary.json"

EXPECTED_BC_DAMAGE = 5165134.682363356
EXPECTED_BC_DPS = 43042.78901969464
REQUESTED_CHUNK_TIMESTEPS = 10000
ACTUAL_CHUNK_TIMESTEPS = 10240
ROLLOUT_GRANULARITY = 512


def main() -> None:
    from rl.guarded_ppo import (
        all_records,
        build_best_manifest,
        build_leaderboard,
        load_plan,
        read_sb3_model_data,
        select_best_candidate,
        sha256_file,
        validate_checkpoint_sidecar,
        verify_resume_state,
    )

    plan = load_plan(PLAN_PATH)
    state = _read_json(STATE_PATH)

    checkpoint_records = _checkpoint_records(state)
    if len(checkpoint_records) != 30:
        raise AssertionError(f"Expected 30 guarded checkpoints, found {len(checkpoint_records)}")

    by_branch = {branch["branch_id"]: branch for branch in plan["branches"]}
    for branch_id, records in _records_by_branch(checkpoint_records).items():
        previous_model_path: Path | None = None
        for record in sorted(records, key=lambda item: int(item["chunk_index"])):
            branch = by_branch[branch_id]
            model_path = ROOT / record["checkpoint_path"]
            sidecar_path = ROOT / record["metadata_path"]
            model_data = read_sb3_model_data(model_path)
            chunk_index = int(record["chunk_index"])
            actual_model_num_timesteps = int(model_data["num_timesteps"])
            requested_cumulative = chunk_index * int(branch["chunk_timesteps"])
            previous_num_timesteps = (
                int(read_sb3_model_data(previous_model_path)["num_timesteps"]) if previous_model_path else 0
            )
            actual_chunk_timesteps = actual_model_num_timesteps - previous_num_timesteps
            expected_seed = int(branch["seed"]) + chunk_index - 1
            if int(model_data["seed"]) != expected_seed:
                raise AssertionError(f"{model_path} internal seed mismatch")
            _add_timestep_fields(
                record,
                requested_chunk=int(branch["chunk_timesteps"]),
                requested_cumulative=requested_cumulative,
                actual_chunk=actual_chunk_timesteps,
                actual_model_num_timesteps=actual_model_num_timesteps,
                rollout_granularity=int(branch["n_steps"]),
            )
            sidecar = _read_json(sidecar_path)
            _add_timestep_fields(
                sidecar,
                requested_chunk=int(branch["chunk_timesteps"]),
                requested_cumulative=requested_cumulative,
                actual_chunk=actual_chunk_timesteps,
                actual_model_num_timesteps=actual_model_num_timesteps,
                rollout_granularity=int(branch["n_steps"]),
            )
            _write_json(sidecar_path, sidecar)
            record["metadata_sha256"] = sha256_file(sidecar_path)
            record["checkpoint_sha256"] = sha256_file(model_path)
            record["model_sha256"] = record["checkpoint_sha256"]
            validate_checkpoint_sidecar(
                branch=branch,
                chunk_index=chunk_index,
                plan_path=PLAN_PATH,
                model_path=model_path,
                metadata_path=sidecar_path,
                parent_model_path=_parent_model_path(state, branch, chunk_index),
            )
            previous_model_path = model_path

    state["completed_experiment_provenance"] = {
        "schema_version": "guarded_ppo_completed_experiment_provenance_v110",
        "source_plan_path": "data/guarded_ppo_experiment_plan_v109.json",
        "source_plan_sha256": sha256_file(PLAN_PATH),
        "trained_branch_count": 3,
        "trained_checkpoint_count": 30,
        "requested_aggregate_timesteps": 300000,
        "actual_aggregate_model_timesteps": 307200,
        "requested_final_timesteps_per_branch": 100000,
        "actual_final_model_timesteps_per_branch": 102400,
        "rollout_granularity": ROLLOUT_GRANULARITY,
        "guarded_long_experiment_executed": True,
        "failed_chunk_count": 0,
        "global_optimum_proven": False,
    }
    _sync_prior_ppo_incumbent(state)
    state["global_best"] = build_best_manifest(
        select_best_candidate(all_records(state)),
        reason="completed guarded PPO v109 ingestion; verified immutable BC tie rule",
    )
    _write_json(STATE_PATH, state)

    leaderboard = build_leaderboard(state)
    if LEADERBOARD_PATH.exists():
        existing = _read_json(LEADERBOARD_PATH)
        leaderboard["updated_at"] = existing.get("updated_at", leaderboard["updated_at"])
    _write_json(LEADERBOARD_PATH, leaderboard)
    _write_json(BEST_PATH, state["global_best"])

    _write_prior_ppo_sidecar()
    final_summary = _build_final_summary(plan, state)
    _write_json(FINAL_SUMMARY_PATH, final_summary)
    FINAL_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINAL_REPORT_PATH.write_text(_render_report(final_summary), encoding="utf-8")

    progress = _read_json(ROOT / "PROJECT_PROGRESS_STATE.json")
    _update_progress(progress, final_summary)
    _write_json(ROOT / "PROJECT_PROGRESS_STATE.json", progress)

    verify_resume_state(_read_json(STATE_PATH), plan_path=PLAN_PATH, plan=plan, output_root=ROOT)
    print("ingest_guarded_ppo_v109_completed_experiment ok")


def _add_timestep_fields(
    target: dict[str, Any],
    *,
    requested_chunk: int,
    requested_cumulative: int,
    actual_chunk: int,
    actual_model_num_timesteps: int,
    rollout_granularity: int,
) -> None:
    overshoot = actual_model_num_timesteps - requested_cumulative
    target["requested_chunk_timesteps"] = requested_chunk
    target["requested_cumulative_timesteps"] = requested_cumulative
    target["actual_chunk_timesteps"] = actual_chunk
    target["actual_model_num_timesteps"] = actual_model_num_timesteps
    target["rollout_granularity"] = rollout_granularity
    target["timestep_overshoot"] = overshoot
    target["timestep_overshoot_ratio"] = float(overshoot) / float(requested_cumulative)


def _write_prior_ppo_sidecar() -> None:
    from rl.demo_contract import file_sha256
    from rl.guarded_ppo import read_sb3_model_data

    summary = _read_json(PRIOR_PPO_SUMMARY)
    metadata = dict(summary["model_training_metadata"])
    model_data = read_sb3_model_data(PRIOR_PPO_MODEL)
    metadata.update(
        {
            "model_path": "models/maskable_ppo_candidate_after_bc_v105.zip",
            "ppo_model_path": "models/maskable_ppo_candidate_after_bc_v105.zip",
            "source_bc_model": "models/maskable_ppo_bc_v105.zip",
            "source_bc_model_sha256": "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e",
            "model_sha256": file_sha256(PRIOR_PPO_MODEL),
            "ppo_model_sha256": file_sha256(PRIOR_PPO_MODEL),
            "requested_seed": 42,
            "actual_saved_model_seed": int(model_data["seed"]),
            "actual_model_seed": int(model_data["seed"]),
            "seed": 42,
            "requested_timesteps": 100000,
            "actual_model_num_timesteps": int(model_data["num_timesteps"]),
            "timesteps": 100000,
            "requested_chunk_timesteps": 100000,
            "requested_cumulative_timesteps": 100000,
            "actual_chunk_timesteps": int(model_data["num_timesteps"]),
            "rollout_granularity": int(model_data["n_steps"]),
            "timestep_overshoot": int(model_data["num_timesteps"]) - 100000,
            "timestep_overshoot_ratio": (int(model_data["num_timesteps"]) - 100000) / 100000.0,
            "provenance_correction": "Model-specific sidecar records requested seed/timesteps separately from actual SB3 saved model seed/num_timesteps.",
        }
    )
    _write_json(PRIOR_PPO_SIDECAR, metadata)


def _sync_prior_ppo_incumbent(state: dict[str, Any]) -> None:
    summary = _read_json(PRIOR_PPO_SUMMARY)
    for record in state.get("incumbents", []):
        if record.get("kind") != "prior_regressed_ppo_model":
            continue
        record["model_training_metadata_source"] = summary.get("model_training_metadata_source")
        record["model_training_metadata_path"] = summary.get("model_training_metadata_path")
        record["model_metadata_mismatches"] = summary.get("model_metadata_mismatches")
        record["model_space_mismatches"] = summary.get("model_space_mismatches")
        record["final_combat_time"] = summary.get("final_time")
        record["total_damage"] = summary.get("total_damage")
        record["dps"] = summary.get("dps")
        record["selected_sequence_sha256"] = summary.get("selected_sequence_sha256")
        record["resolved_sequence_sha256"] = summary.get("resolved_sequence_sha256")
        record["selected_action_count"] = summary.get("selected_action_count")
        record["resolved_action_count"] = summary.get("resolved_action_count")
        break


def _build_final_summary(plan: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    records = _checkpoint_records(state)
    branches: dict[str, Any] = {}
    for branch in plan["branches"]:
        branch_id = branch["branch_id"]
        branch_records = sorted(
            [record for record in records if record["branch_id"] == branch_id],
            key=lambda item: int(item["chunk_index"]),
        )
        checkpoints = [
            {
                "chunk_index": int(record["chunk_index"]),
                "requested_cumulative_timesteps": int(record["requested_cumulative_timesteps"]),
                "actual_model_num_timesteps": int(record["actual_model_num_timesteps"]),
                "total_damage": record["total_damage"],
                "dps": record["dps"],
                "model_path": record["model_path"],
                "model_sha256": record["model_sha256"],
                "summary_path": record["summary_path"],
                "timeline_path": record["timeline_path"],
                "selected_sequence_sha256": record["selected_sequence_sha256"],
                "resolved_sequence_sha256": record["resolved_sequence_sha256"],
                "route_agreement_ratio_diagnostic_only": record["route_agreement_ratio_diagnostic_only"],
            }
            for record in branch_records
        ]
        best = max(branch_records, key=lambda item: float(item["total_damage"]))
        final = branch_records[-1]
        branches[branch_id] = {
            "role": branch["role"],
            "checkpoint_count": len(branch_records),
            "checkpoints": checkpoints,
            "best_checkpoint": {
                "chunk_index": int(best["chunk_index"]),
                "requested_cumulative_timesteps": int(best["requested_cumulative_timesteps"]),
                "actual_model_num_timesteps": int(best["actual_model_num_timesteps"]),
                "total_damage": best["total_damage"],
                "ratio_vs_bc": float(best["total_damage"]) / EXPECTED_BC_DAMAGE,
                "model_path": best["model_path"],
                "model_sha256": best["model_sha256"],
            },
            "final_checkpoint": {
                "chunk_index": int(final["chunk_index"]),
                "requested_cumulative_timesteps": int(final["requested_cumulative_timesteps"]),
                "actual_model_num_timesteps": int(final["actual_model_num_timesteps"]),
                "total_damage": final["total_damage"],
                "ratio_vs_bc": float(final["total_damage"]) / EXPECTED_BC_DAMAGE,
                "model_path": final["model_path"],
                "model_sha256": final["model_sha256"],
            },
        }
    prior = _read_json(ROOT / "results" / "ppo_100k_evaluation_summary.json")
    return {
        "schema_version": "guarded_ppo_completed_experiment_summary_v110",
        "candidate": "110",
        "source_candidate": "109",
        "latest_verified_baseline": "109",
        "plan_path": "data/guarded_ppo_experiment_plan_v109.json",
        "plan_sha256": state["plan_sha256"],
        "objective": "deterministic_120s_total_damage_only",
        "incumbents": {
            "manual_baseline": {
                "summary_path": "results/manual_120s_baseline_v104_summary.json",
                "total_damage": 5165134.682363359,
            },
            "verified_bc_model": {
                "model_path": "models/maskable_ppo_bc_v105.zip",
                "model_sha256": "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e",
                "total_damage": EXPECTED_BC_DAMAGE,
                "dps": EXPECTED_BC_DPS,
            },
            "prior_unguarded_ppo_100k": {
                "model_path": "models/maskable_ppo_candidate_after_bc_v105.zip",
                "model_sha256": "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513",
                "total_damage": prior["total_damage"],
                "dps": prior["dps"],
                "requested_seed": 42,
                "actual_saved_model_seed": 11,
                "requested_timesteps": 100000,
                "actual_model_num_timesteps": 100352,
            },
        },
        "timestep_budget": {
            "requested_chunk_timesteps": REQUESTED_CHUNK_TIMESTEPS,
            "actual_chunk_timesteps": ACTUAL_CHUNK_TIMESTEPS,
            "rollout_granularity": ROLLOUT_GRANULARITY,
            "requested_final_timesteps_per_branch": 100000,
            "actual_final_model_timesteps_per_branch": 102400,
            "timestep_overshoot_per_branch": 2400,
            "timestep_overshoot_ratio": 0.024,
            "requested_aggregate_timesteps": 300000,
            "actual_aggregate_model_timesteps": 307200,
        },
        "branches": branches,
        "winner": {
            "winner_kind": "verified_bc_model",
            "model_path": "models/maskable_ppo_bc_v105.zip",
            "total_damage": EXPECTED_BC_DAMAGE,
            "dps": EXPECTED_BC_DPS,
            "selection_rule": "Verified immutable incumbent wins exact/tolerance ties.",
        },
        "no_guarded_checkpoint_exceeded_bc": all(float(record["total_damage"]) <= EXPECTED_BC_DAMAGE + 1e-6 for record in records),
        "global_optimum_proven": False,
        "route_similarity_objective": False,
        "route_similarity_usage": "diagnostic_only_not_used_for_winner_selection",
        "interpretation": (
            "The completed guarded PPO budget found no checkpoint above the verified BC/manual result. "
            "The scratch control remains far below BC under this budget. This is useful negative evidence for this PPO configuration, not a proof of global optimality."
        ),
    }


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Guarded PPO v109 Completed Experiment Results",
        "",
        "Candidate 110 ingests the externally reviewed completed v109 guarded PPO experiment. Candidate 110 remains pending external review.",
        "",
        "## Winner",
        "",
        f"- Winner: `{summary['winner']['winner_kind']}`",
        f"- Model: `{summary['winner']['model_path']}`",
        f"- Total damage: `{summary['winner']['total_damage']}`",
        f"- DPS: `{summary['winner']['dps']}`",
        "- Global optimum proven: `false`",
        "",
        "## Timestep Budget",
        "",
        f"- Requested aggregate timesteps: `{summary['timestep_budget']['requested_aggregate_timesteps']}`",
        f"- Actual aggregate SB3 model timesteps: `{summary['timestep_budget']['actual_aggregate_model_timesteps']}`",
        f"- Rollout granularity: `{summary['timestep_budget']['rollout_granularity']}`",
        f"- Per-branch overshoot: `{summary['timestep_budget']['timestep_overshoot_per_branch']}` (`{summary['timestep_budget']['timestep_overshoot_ratio']}`)",
        "",
        "## Branch Results",
        "",
        "| Branch | Best requested step | Best damage | Best / BC | Final requested step | Final damage | Final / BC |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for branch_id, branch in summary["branches"].items():
        best = branch["best_checkpoint"]
        final = branch["final_checkpoint"]
        lines.append(
            f"| `{branch_id}` | {best['requested_cumulative_timesteps']} | {best['total_damage']} | "
            f"{best['ratio_vs_bc']} | {final['requested_cumulative_timesteps']} | {final['total_damage']} | {final['ratio_vs_bc']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary["interpretation"],
            "",
            "Route similarity remains diagnostic only and is not part of winner selection.",
        ]
    )
    return "\n".join(lines) + "\n"


def _update_progress(progress: dict[str, Any], summary: dict[str, Any]) -> None:
    progress["status"]["latest_verified_archive"] = "ww-dps-simulator-2(109).zip"
    progress["status"]["latest_verified_baseline_label"] = "109"
    progress["status"]["current_task_status"] = "implemented_tests_passed_pending_external_review"
    progress["status"]["current_task"] = "completed guarded PPO v109 experiment ingestion and reporting"
    progress["status"]["current_task_expected_next_archive"] = "110"
    progress["status"]["candidate_expected_next_archive"] = "ww-dps-simulator-2-110.zip"
    progress["current_in_progress_task"] = {
        "task": "completed guarded PPO v109 experiment ingestion, provenance correction, and reporting",
        "status": "implemented_tests_passed_pending_external_review",
        "candidate": "110",
        "external_review_required": True,
        "external_verification_claimed": False,
        "latest_externally_verified_baseline": "109",
        "baseline_archive": "ww-dps-simulator-2(109).zip",
        "candidate_expected_next_archive": "ww-dps-simulator-2-110.zip",
        "guarded_long_experiment_executed": True,
        "requested_aggregate_ppo_budget": 300000,
        "actual_aggregate_sb3_model_timesteps": 307200,
        "completed_guarded_checkpoint_count": 30,
        "failed_chunk_count": 0,
        "current_best_model": "models/maskable_ppo_bc_v105.zip",
        "current_best_result": EXPECTED_BC_DAMAGE,
        "winner": "verified_bc_model",
        "objective": "deterministic_120s_total_damage_only",
        "global_optimum_claimed": False,
        "route_similarity_objective": False,
        "character_specific_reward": False,
        "rollback_enabled": False,
        "plan_path": "data/guarded_ppo_experiment_plan_v109.json",
        "plan_sha256": summary["plan_sha256"],
        "final_summary_path": "results/guarded_ppo_v109/final_experiment_summary.json",
        "final_report_path": "reports/guarded_ppo_experiment_v109_results.md",
        "notes": [
            "Candidate 109 is now the latest externally verified baseline.",
            "Candidate 110 ingests the completed v109 guarded PPO experiment and remains pending external review.",
            "All 30 guarded PPO checkpoints completed with no failed chunks.",
            "Requested aggregate PPO budget was 300000 timesteps; actual SB3 model timesteps total 307200 due rollout rounding.",
            "No guarded checkpoint exceeded the verified immutable BC model.",
            "Route similarity remains diagnostic only and does not influence winner selection.",
            "No combat formulas, action data, reward formula, observation schema, route, BC NPZ, BC model, prior PPO model, guarded checkpoint model, or runtime executor model bytes were modified.",
        ],
        "next_after_external_verification": "implement an independent Beam Search or MCTS comparison and compare its best 120-second total damage against manual/BC/all guarded PPO checkpoints before considering more PPO budget",
    }
    for item in progress.get("candidate_history", []):
        if item.get("candidate") == "109":
            item.update(
                {
                    "status": "externally_verified_complete",
                    "latest_externally_verified_baseline": "109",
                    "external_review_status": "passed",
                    "external_verification_claimed": True,
                    "external_verification_label": "109",
                    "baseline_archive": "ww-dps-simulator-2(109).zip",
                    "guarded_long_experiment_executed": True,
                    "completed_guarded_checkpoint_count": 30,
                    "requested_aggregate_ppo_budget": 300000,
                    "actual_aggregate_sb3_model_timesteps": 307200,
                    "winner": "verified_bc_model",
                    "winner_model": "models/maskable_ppo_bc_v105.zip",
                    "archive_path": "../ww-dps-simulator-2(109).zip",
                }
            )
            break
    if not any(item.get("candidate") == "110" for item in progress.get("candidate_history", [])):
        progress.setdefault("candidate_history", []).append(
            {
                "candidate": "110",
                "task": "completed guarded PPO v109 experiment ingestion and reporting",
                "status": "implemented_tests_passed_pending_external_review",
                "latest_externally_verified_baseline": "109",
                "external_review_status": "pending",
                "external_verification_claimed": False,
                "guarded_long_experiment_executed": True,
                "completed_guarded_checkpoint_count": 30,
                "requested_aggregate_ppo_budget": 300000,
                "actual_aggregate_sb3_model_timesteps": 307200,
                "winner": "verified_bc_model",
                "archive_path": "../ww-dps-simulator-2-110.zip",
            }
        )
    progress["next_planned_task"] = "after candidate 110 external review, implement independent Beam Search or MCTS comparison against manual, BC, and all guarded PPO checkpoints"
    progress["next_planned_tasks"] = [
        {"task": "external review of candidate 110"},
        {"task": "implement an independent Beam Search or MCTS comparison"},
        {"task": "compare search best 120-second total damage against manual, BC, and all guarded PPO checkpoints"},
        {"task": "allocate further PPO budget only if a new reviewed hypothesis justifies it"},
    ]


def _checkpoint_records(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        chunk
        for branch_state in state["branches"].values()
        for chunk in branch_state["chunks"]
        if chunk.get("kind") == "guarded_ppo_checkpoint"
    ]


def _records_by_branch(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["branch_id"], []).append(record)
    return grouped


def _parent_model_path(state: dict[str, Any], branch: dict[str, Any], chunk_index: int) -> Path | None:
    if chunk_index == 1:
        init = branch.get("initialization") or {}
        return ROOT / init["source_model_path"] if init.get("mode") == "model" else None
    previous = next(
        chunk
        for chunk in state["branches"][branch["branch_id"]]["chunks"]
        if int(chunk.get("chunk_index", -1)) == chunk_index - 1
    )
    return ROOT / previous["checkpoint_path"]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
