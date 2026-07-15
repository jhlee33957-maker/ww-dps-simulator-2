from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    progress = json.loads((root / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    current = progress["current_in_progress_task"]
    completed = current["candidate_116_completed_beam"]
    assert status["latest_externally_verified_baseline"] == "117"
    assert status["current_candidate"] == "118"
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
    assert current["mcts_executed"] is False
    assert current["candidate_117_mcts"]["calibration_20k_executed"] is True
    assert current["global_optimum_claimed"] is False
    print("project_progress_beam_completed_v116_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
