from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    progress = json.loads((root / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    current = progress["current_in_progress_task"]
    completed = current["candidate_116_completed_beam"]
    assert status["latest_externally_verified_baseline"] == "121"
    assert status["current_candidate"] == "122"
    assert status["current_task_status"] == "candidate_pending_external_review"
    assert completed["termination_status"] == "completed_search"
    assert completed["expansions"] == 4908270
    assert completed["completed_120s_route_count"] == 128
    assert completed["winning_route_id"] == "67a4250b3b8d0de9"
    assert completed["winning_damage"] == 5651892.274552992
    assert completed["winning_dps"] == 47099.1022879416
    assert current["long_v115_resume_executed"] is True
    assert current["overall_project_winner"]["winner_kind"] == "beam_search_route"
    assert current["best_trained_model"]["model_path"].endswith("step_000090000.zip")
    history = next(item for item in progress["candidate_history"] if item.get("candidate") == "116")
    assert history["status"] == "externally_verified_complete"
    assert history["external_review_status"] == "passed"
    assert history["winner_route_id"] == completed["winning_route_id"]
    assert history["winner_total_damage"] == completed["winning_damage"]
    manifest = root / history["result_manifest_path"]
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == history["result_manifest_sha256"]
    assert history["full_result_inventory_entry_digest_sha256"] == "19e808db96952ea9405ed4d9699075073fbf61dcbc68a8b12e83acfa3b2ed854"
    assert current["candidate_119_mcts"]["production_search_executed"] is True
    assert current["candidate_117_mcts"]["calibration_20k_executed"] is True
    assert current["global_optimum_claimed"] is False
    print("project_progress_beam_completed_v116_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
