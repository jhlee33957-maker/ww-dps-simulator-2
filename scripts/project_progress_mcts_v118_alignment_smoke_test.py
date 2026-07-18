from __future__ import annotations
import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    progress = json.loads((root / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "121"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-121(19).zip"
    assert status["current_candidate"] == "122" and status["current_task_status"] == "candidate_pending_external_review"
    current = progress["current_in_progress_task"]
    calibration = current["candidate_117_mcts"]; candidate = current["candidate_118_mcts"]
    assert calibration["calibration_20k_executed"] and calibration["simulations_completed"] == 20000
    assert calibration["completed_rollouts"] == 20000 and calibration["invalid_rollouts"] == 0
    assert calibration["best_route_id"] == "5aab329ce5b526a7" and calibration["calibration_only"]
    manifest = root / calibration["compact_manifest_path"]
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == calibration["compact_manifest_sha256"]
    plan = root / candidate["production_plan_path"]
    assert hashlib.sha256(plan.read_bytes()).hexdigest() == candidate["production_plan_sha256"]
    assert candidate["production_plan_ready"] and candidate["production_search_executed"]
    assert candidate["external_review_status"] == "passed"
    assert candidate["seeds"] == [118001, 118002, 118003] and candidate["independent_empty_tree_and_mast"]
    assert candidate["current_overall_winner_route_id"] == "67a4250b3b8d0de9" and not candidate["global_optimum_claimed"]
    history = next(item for item in progress["candidate_history"] if item.get("candidate") == "118")
    assert history["candidate"] == "118" and history["status"] == "externally_verified_complete"
    assert history["external_review_status"] == "passed" and history["external_verification_claimed"] is True
    assert history["production_search_executed"] is True
    assert progress["current_in_progress_task"]["candidate_119_mcts"]["production_seeds_completed"] == 3
    print("project_progress_mcts_v118_alignment_smoke_test ok baseline=121 candidate=122 production=true")


if __name__ == "__main__": main()
