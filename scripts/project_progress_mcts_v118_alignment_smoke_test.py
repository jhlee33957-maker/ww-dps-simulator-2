from __future__ import annotations
import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    progress = json.loads((root / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "117"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-117(1).zip"
    assert status["current_candidate"] == "118" and status["current_task_status"] == "candidate_pending_external_review"
    current = progress["current_in_progress_task"]
    calibration = current["candidate_117_mcts"]; candidate = current["candidate_118_mcts"]
    assert calibration["calibration_20k_executed"] and calibration["simulations_completed"] == 20000
    assert calibration["completed_rollouts"] == 20000 and calibration["invalid_rollouts"] == 0
    assert calibration["best_route_id"] == "5aab329ce5b526a7" and calibration["calibration_only"]
    manifest = root / calibration["compact_manifest_path"]
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == calibration["compact_manifest_sha256"]
    plan = root / candidate["production_plan_path"]
    assert hashlib.sha256(plan.read_bytes()).hexdigest() == candidate["production_plan_sha256"]
    assert candidate["production_plan_ready"] and not candidate["production_search_executed"]
    assert candidate["pending_review_note"] == (
        "candidate-118 cleanup validation made self-contained; external review ZIP is ingestion evidence, "
        "not a cleanup runtime dependency; fresh source archive now executes the cleanup fixture test."
    )
    assert candidate["seeds"] == [118001, 118002, 118003] and candidate["independent_empty_tree_and_mast"]
    assert candidate["current_overall_winner_route_id"] == "67a4250b3b8d0de9" and not candidate["global_optimum_claimed"]
    history = progress["candidate_history"][-1]
    assert history["candidate"] == "118" and history["status"] == "candidate_pending_external_review"
    print("project_progress_mcts_v118_alignment_smoke_test ok baseline=117 candidate=118 production=false")


if __name__ == "__main__": main()
