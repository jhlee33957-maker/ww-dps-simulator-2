from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.guarded_ppo import (  # noqa: E402
    DEFAULT_PLAN_PATH,
    load_plan,
    path_from_state,
    read_sb3_model_data,
    sha256_file,
    canonicalize_guarded_path,
    validate_checkpoint_sidecar,
    verify_resume_state,
)


RESULTS = ROOT / "results" / "guarded_ppo_v109"
MODELS = ROOT / "models" / "guarded_ppo_v109"
EXPECTED_PLAN_SHA256 = "0306c734347e49460fd7273bce546eed80a2db657e460eb707f5cab961a9e0e6"
EXPECTED_BC_DAMAGE = 5165134.682363356
EXPECTED_BRANCHES = {
    "bc_conservative_seed_11": {
        "seeds": list(range(11, 21)),
        "best": (1, 5165134.682363356, 1.0),
        "final": (10, 5134470.883053988, 0.9940633107953465),
        "checkpoints": {
            1: 5165134.682363356,
            2: 5165134.682363356,
            7: 5156315.608505706,
            10: 5134470.883053988,
        },
    },
    "bc_exploratory_seed_73": {
        "seeds": list(range(73, 83)),
        "best": (1, 5165134.682363356, 1.0),
        "final": (10, 4777468.267968915, 0.9249455361312939),
        "checkpoints": {
            1: 5165134.682363356,
            2: 5158201.636481964,
            10: 4777468.267968915,
        },
    },
    "scratch_control_seed_137": {
        "seeds": list(range(137, 147)),
        "best": (5, 2566933.375001255, 0.49697317356819243),
        "final": (10, 1816940.651360404, 0.3517702370016508),
        "checkpoints": {
            5: 2566933.375001255,
            10: 1816940.651360404,
        },
    },
}


def main() -> None:
    plan = load_plan(DEFAULT_PLAN_PATH)
    state = _load_json(RESULTS / "experiment_state.json")
    leaderboard = _load_json(RESULTS / "leaderboard.json")
    best = _load_json(RESULTS / "best_checkpoint.json")
    final_summary = _load_json(RESULTS / "final_experiment_summary.json")

    assert sha256_file(DEFAULT_PLAN_PATH) == EXPECTED_PLAN_SHA256
    assert state["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert final_summary["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert final_summary["candidate"] == "110"
    assert final_summary["source_candidate"] == "109"
    assert final_summary["latest_verified_baseline"] == "109"
    assert final_summary["no_guarded_checkpoint_exceeded_bc"] is True
    assert final_summary["global_optimum_proven"] is False
    assert final_summary["route_similarity_objective"] is False
    assert final_summary["route_similarity_usage"] == "diagnostic_only_not_used_for_winner_selection"

    provenance = state["completed_experiment_provenance"]
    assert provenance["trained_branch_count"] == 3
    assert provenance["trained_checkpoint_count"] == 30
    assert provenance["failed_chunk_count"] == 0
    assert provenance["requested_aggregate_timesteps"] == 300000
    assert provenance["actual_aggregate_model_timesteps"] == 307200

    verify_resume_state(state, plan_path=DEFAULT_PLAN_PATH, plan=plan)
    assert len(list(MODELS.glob("*/*.zip"))) == 30
    assert len(list(MODELS.glob("*/*.zip.ppo_metadata.json"))) == 30
    assert len(list((RESULTS / "branches").glob("*/*_summary.json"))) == 30
    assert len(list((RESULTS / "branches").glob("*/*_timeline.csv"))) == 30

    checkpoint_records: list[dict[str, Any]] = []
    branches_by_id = {branch["branch_id"]: branch for branch in plan["branches"]}
    for branch_id, expected in EXPECTED_BRANCHES.items():
        branch = branches_by_id[branch_id]
        records = [
            item
            for item in state["branches"][branch_id]["chunks"]
            if item.get("kind") == "guarded_ppo_checkpoint"
        ]
        assert len(records) == 10
        assert [record["chunk_index"] for record in records] == list(range(1, 11))
        assert [record["actual_model_seed"] for record in records] == expected["seeds"]
        assert [record["actual_model_num_timesteps"] for record in records] == [10240 * index for index in range(1, 11)]
        parent: Path | None = _initial_parent_model_path(branch)
        for record in records:
            checkpoint_records.append(record)
            checkpoint = path_from_state(record["checkpoint_path"])
            sidecar = path_from_state(record["metadata_path"])
            validate_checkpoint_sidecar(
                branch=branch,
                chunk_index=int(record["chunk_index"]),
                plan_path=DEFAULT_PLAN_PATH,
                model_path=checkpoint,
                metadata_path=sidecar,
                parent_model_path=parent,
            )
            _assert_hashes(record, checkpoint, sidecar)
            model_data = read_sb3_model_data(checkpoint)
            assert int(model_data["seed"]) == int(record["actual_model_seed"])
            assert int(model_data["num_timesteps"]) == int(record["actual_model_num_timesteps"])
            assert int(model_data["n_steps"]) == 512
            _assert_summary_and_timeline(record)
            parent = checkpoint
        for chunk_index, damage in expected["checkpoints"].items():
            _assert_close(records[chunk_index - 1]["total_damage"], damage)

    assert len(checkpoint_records) == 30
    assert max(float(record["total_damage"]) for record in checkpoint_records) <= EXPECTED_BC_DAMAGE + 1e-6
    assert best["winner_kind"] == "verified_bc_model"
    assert best["model_path"] == "models/maskable_ppo_bc_v105.zip"
    _assert_close(best["total_damage"], EXPECTED_BC_DAMAGE)
    assert leaderboard["global_best"]["winner_kind"] == "verified_bc_model"
    assert len([item for item in leaderboard["records"] if item.get("kind") == "guarded_ppo_checkpoint"]) == 30

    for branch_id, expected in EXPECTED_BRANCHES.items():
        branch_summary = final_summary["branches"][branch_id]
        assert branch_summary["checkpoint_count"] == 10
        _assert_checkpoint_ref(branch_summary["best_checkpoint"], expected["best"])
        _assert_checkpoint_ref(branch_summary["final_checkpoint"], expected["final"])

    print("guarded_ppo_completed_experiment_integrity_smoke_test ok")


def _assert_hashes(record: dict[str, Any], checkpoint: Path, sidecar: Path) -> None:
    assert sha256_file(checkpoint) == record["checkpoint_sha256"]
    assert sha256_file(sidecar) == record["metadata_sha256"]
    for key in (
        "summary",
        "timeline",
        "evaluation_stdout_log",
        "evaluation_stderr_log",
        "training_stdout_log",
        "training_stderr_log",
    ):
        path_value = record.get(f"{key}_path")
        sha_value = record.get(f"{key}_sha256")
        if path_value:
            assert sha256_file(path_from_state(path_value)) == sha_value


def _assert_summary_and_timeline(record: dict[str, Any]) -> None:
    summary = _load_json(path_from_state(record["summary_path"]))
    assert path_from_state(record["timeline_path"]).exists()
    assert summary["model_training_metadata_source"] == "ppo_model_sidecar"
    assert canonicalize_guarded_path(summary["model_training_metadata_path"]) == record["metadata_path"]
    assert summary["model_metadata_mismatches"] == {}
    assert summary["model_space_mismatches"] == {}
    assert summary["selected_sequence_sha256"] == record["selected_sequence_sha256"]
    assert summary["resolved_sequence_sha256"] == record["resolved_sequence_sha256"]
    _assert_close(summary["final_time"], 120.0)
    _assert_close(summary["total_damage"], record["total_damage"])
    role_breakdown = summary["effective_damage_role_breakdown"]
    _assert_close(role_breakdown["total_damage_delta"], 0.0)


def _assert_checkpoint_ref(payload: dict[str, Any], expected: tuple[int, float, float]) -> None:
    chunk_index, damage, ratio = expected
    assert payload["chunk_index"] == chunk_index
    _assert_close(payload["total_damage"], damage)
    _assert_close(payload["ratio_vs_bc"], ratio)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _initial_parent_model_path(branch: dict[str, Any]) -> Path | None:
    initialization = branch.get("initialization") or {}
    if initialization.get("mode") != "model":
        return None
    return ROOT / initialization["source_model_path"]


def _assert_close(actual: object, expected: float, *, tolerance: float = 1e-6) -> None:
    assert abs(float(actual) - expected) <= tolerance, (actual, expected)


if __name__ == "__main__":
    main()
