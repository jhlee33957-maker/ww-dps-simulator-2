from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    progress = json.loads((root / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "119"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-119(1).zip"
    assert status["latest_verified_archive_sha256"] == "7248290f4b3f3f8107cfd10ff1b5e539167721b19a182fdb69b875221ce394ae"
    assert status["current_candidate"] == "120" and status["current_task_status"] == "candidate_pending_external_review"
    current = progress["current_in_progress_task"]
    production = current["candidate_119_mcts"]
    assert production["pending_review_note"] == (
        "candidate-119 first package incorrectly executed only the new fresh-extraction checks; "
        "full legacy regression coverage and history-aware alignment tests restored before external verification."
    )
    assert production["production_search_executed"] and production["production_seeds_completed"] == 3
    assert production["production_simulations_completed"] == 150000 and production["production_invalid_rollouts"] == 0
    assert production["best_seed"] == 118003 and production["best_route_id"] == "d3dcc3f4b372ac5d"
    assert production["best_damage"] == 4647724.703247974 and production["extension_recommended"] is False
    assert production["production_finalized"] and production["global_optimum_claimed"] is False
    assert production["external_review_status"] == "passed"
    assert production["verified_archive"] == "ww-dps-simulator-2-119(1).zip"
    manifest = root / production["compact_manifest_path"]
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == production["compact_manifest_sha256"]
    assert current["overall_project_winner"]["route_id"] == "67a4250b3b8d0de9"
    assert current["best_trained_model"]["model_path"].endswith("step_000090000.zip")
    history_119 = [item for item in progress["candidate_history"] if item.get("candidate") == "119"][-1]
    assert history_119["status"] == "externally_verified_complete"
    assert history_119["external_review_status"] == "passed"
    print("project_progress_mcts_v119_alignment_smoke_test ok baseline=119 current_candidate=120 production=3/3 winner=beam")


if __name__ == "__main__": main()
