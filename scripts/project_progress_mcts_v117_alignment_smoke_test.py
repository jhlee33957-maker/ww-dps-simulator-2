from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    progress = json.loads((root / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "118"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-118(1).zip"
    assert status["latest_verified_archive_sha256"] == "0f3c92c4cd28bf869a6e397c63254a1af87a7ef1277ee9936f148e956c2f7621"
    assert status["current_candidate"] == "119"
    assert status["current_task_status"] == "candidate_pending_external_review"
    current = progress["current_in_progress_task"]
    assert current["overall_project_winner"]["winner_kind"] == "beam_search_route"
    assert current["best_trained_model"]["model_path"].endswith("step_000090000.zip")
    mcts = current["candidate_117_mcts"]
    assert mcts["infrastructure_implemented"] is True
    assert mcts["calibration_20k_executed"] is True and mcts["completed_result_available"] is True
    for key in ("production_search_executed", "new_beam_search_executed", "bc_training_executed",
                "ppo_training_executed", "global_optimum_claimed"):
        assert mcts[key] is False, key
    for key in ("manual_route_guidance", "bc_ppo_policy_guidance", "beam_policy_guidance", "beam_route_guidance"):
        assert mcts[key] is False, key
    history = next(item for item in progress["candidate_history"] if item["candidate"] == "117")
    assert history["status"] == "externally_verified_complete" and history["external_review_status"] == "passed"
    assert history["first_candidate_117_bounded_probe_failed"] is True
    assert "corrected before external verification" in history["pre_external_verification_correction_note"]
    assert history["plan_sha256"] == mcts["plan_sha256"]
    assert current["candidate_118_mcts"]["production_search_executed"] is True
    assert (root / current["candidate_116_completed_beam"]["cleanup_receipt_path"]).is_file()
    raw = root / "results/mcts_v117_32gb/calibration_20k_seed_117001"
    assert raw.is_dir() or (root / "results/mcts_v117_calibration_20k_v118/result_manifest.json").is_file()
    print("project_progress_mcts_v117_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
