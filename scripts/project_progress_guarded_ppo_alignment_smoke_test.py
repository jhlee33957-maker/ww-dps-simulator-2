from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    state = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = state["status"]
    assert status["latest_verified_baseline_label"] == "108"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2(108).zip"
    assert status["current_task_expected_next_archive"] == "109"
    assert status["candidate_expected_next_archive"] == "ww-dps-simulator-2-109.zip"

    current = state["current_in_progress_task"]
    assert current["candidate"] == "109"
    assert current["external_review_required"] is True
    assert current["guarded_long_experiment_executed"] is False
    assert current["objective"] == "deterministic_120s_total_damage_only"
    assert current["current_best_model"] == "models/maskable_ppo_bc_v105.zip"
    assert current["prior_ppo_status"] == "valid_but_regressed"
    assert current["global_optimum_claimed"] is False
    assert current["route_similarity_objective"] is False
    assert current["character_specific_reward"] is False
    assert current["rollback_enabled"] is False
    assert current["plan_path"] == "data/guarded_ppo_experiment_plan_v109.json"
    assert current["plan_sha256"] == "0306c734347e49460fd7273bce546eed80a2db657e460eb707f5cab961a9e0e6"
    assert current["branch_ids"] == [
        "bc_conservative_seed_11",
        "bc_exploratory_seed_73",
        "scratch_control_seed_137",
    ]
    history_108 = next(item for item in state["candidate_history"] if item["candidate"] == "108")
    assert history_108["status"] == "externally_verified_complete"
    assert history_108["external_review_status"] == "passed"
    assert history_108["external_verification_claimed"] is True
    assert history_108["external_verification_label"] == "108"
    assert history_108["baseline_archive"] == "ww-dps-simulator-2(108).zip"
    history_109 = next(item for item in state["candidate_history"] if item["candidate"] == "109")
    assert history_109["status"] == "implemented_tests_passed_pending_external_review"
    assert history_109["guarded_long_experiment_executed"] is False
    assert history_109["plan_sha256"] == current["plan_sha256"]
    assert history_109["archive_path"] == "../ww-dps-simulator-2-109.zip"
    notes = "\n".join(current["notes"])
    for required in (
        "Cross-platform guarded result ingestion now canonicalizes legacy Windows and POSIX project paths",
        "Native project-relative resolution now precedes generic anchor recovery for guarded paths",
        "Parent directories named data no longer corrupt guarded canonical paths",
        "Strict guarded PPO checkpoint sidecar provenance validation now rejects missing required fields",
        "Strict sidecar contract coverage now includes fresh Linux extraction paths",
        "CLI execution-gate validation now uses bounded in-process parser validation",
        "Dry-run step-0 output now reports one shared verified BC alias evaluation",
    ):
        assert required in notes
    next_tasks = state["next_planned_tasks"]
    assert [item["task"] for item in next_tasks] == [
        "external review of candidate 109",
        "execute the reviewed v109 guarded PPO plan",
        "deterministic evaluation after every 10k chunk and immutable-best comparison against BC",
        "compare guarded PPO results with Beam Search/MCTS afterward",
    ]
    serialized = json.dumps(state, ensure_ascii=False).lower()
    forbidden = [
        "after_candidate_108_external_verification",
        "implement guarded ppo continuation with periodic deterministic evaluation and best-model retention",
        "candidate 108 is pending",
        "\"guarded_long_experiment_executed\": true",
    ]
    for text in forbidden:
        assert text not in serialized, text
    print("project_progress_guarded_ppo_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
