from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = progress["status"]
    current = progress["current_in_progress_task"]
    assert status["latest_verified_baseline_label"] == "112"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-112.zip"
    assert status["current_task_expected_next_archive"] == "113"
    assert status["current_task_status"] == "candidate_pending_external_review"
    assert current["candidate"] == "113"
    assert current["task"] == "32GB low-memory 120-second Beam Search plan and slim runtime workspace"
    assert current["calibration_stage_executed"] is True
    assert current["full_search_stage_executed"] is False
    assert current["mcts_execution"] is False
    assert current["current_best_model"] == "models/maskable_ppo_bc_v105.zip"
    assert current["current_best_result"] == 5165134.682363356
    assert current["global_optimum_claimed"] is False
    assert current["reference_damage_comparison_status"] == "horizon_mismatch_not_comparable"
    assert current["calibration_metrics"]["actual_expansions"] == 381918
    assert current["calibration_best_route"]["route_id"] == "a301f753b3ddf6e4"
    history_111 = next(item for item in progress["candidate_history"] if item["candidate"] == "111")
    history_112 = next(item for item in progress["candidate_history"] if item["candidate"] == "112")
    assert history_111["status"] == "externally_verified_complete"
    assert history_111["external_review_status"] == "passed"
    assert history_111["external_verification_claimed"] is True
    assert history_111["archive_sha256"] == "9577ee38ebbf655d51ab854970f01d6f10920b48b1abfd947080972592bc93a6"
    assert history_111["validation_summary"]["status"] == "externally_verified_complete"
    assert history_111["validation_summary"]["archive_exact_validation_passed"] is True
    assert history_111["validation_summary"]["canonical_beam_search_results_written"] is False
    assert history_112["status"] == "externally_verified_complete"
    assert history_112["calibration_stage_executed"] is True
    assert [item["task"] for item in progress["next_planned_tasks"]] == [
        "external review of candidate 113",
        "build the slim runtime workspace",
        "run the reviewed 32GB low-memory Beam plan to 3M expansions",
        "review memory, runtime, and best completed 120-second result",
        "resume to 5M only if useful, then run MCTS as an independent complementary search",
    ]
    print("project_progress_beam_search_calibration_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
