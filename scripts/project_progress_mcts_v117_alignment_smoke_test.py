from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    progress = json.loads((root / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "116"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-116.zip"
    assert status["latest_verified_archive_sha256"] == "b652b9bb2f1fff1678895ae693b21241875de1374f19766d104c8572c761ab24"
    assert status["current_candidate"] == "117"
    assert status["current_task_status"] == "candidate_pending_external_review"
    current = progress["current_in_progress_task"]
    assert current["overall_project_winner"]["winner_kind"] == "beam_search_route"
    assert current["best_trained_model"]["model_path"].endswith("step_000090000.zip")
    mcts = current["candidate_117_mcts"]
    assert mcts["infrastructure_implemented"] is True
    for key in ("calibration_20k_executed", "production_search_executed", "completed_result_available",
                "new_beam_search_executed", "bc_training_executed", "ppo_training_executed", "global_optimum_claimed"):
        assert mcts[key] is False, key
    for key in ("manual_route_guidance", "bc_ppo_policy_guidance", "beam_policy_guidance", "beam_route_guidance"):
        assert mcts[key] is False, key
    history = next(item for item in progress["candidate_history"] if item["candidate"] == "117")
    assert history["first_candidate_117_bounded_probe_failed"] is True
    assert "corrected before external verification" in history["pre_external_verification_correction_note"]
    assert (root / current["candidate_116_completed_beam"]["cleanup_receipt_path"]).is_file()
    assert not (root / "results/mcts_v117_32gb/calibration_20k_seed_117001").exists()
    print("project_progress_mcts_v117_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
