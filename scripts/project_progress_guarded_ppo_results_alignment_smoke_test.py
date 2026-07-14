from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "guarded_ppo_v109"
EXPECTED_PLAN_SHA256 = "0306c734347e49460fd7273bce546eed80a2db657e460eb707f5cab961a9e0e6"
EXPECTED_BC_DAMAGE = 5165134.682363356


def main() -> None:
    progress = _load_json(ROOT / "PROJECT_PROGRESS_STATE.json")
    experiment_state = _load_json(RESULTS / "experiment_state.json")
    final_summary = _load_json(RESULTS / "final_experiment_summary.json")
    best = _load_json(RESULTS / "best_checkpoint.json")

    status = progress["status"]
    current = progress["current_in_progress_task"]
    history_110 = next(item for item in progress["candidate_history"] if item["candidate"] == "110")
    history_109 = next(item for item in progress["candidate_history"] if item["candidate"] == "109")
    provenance = experiment_state["completed_experiment_provenance"]

    assert int(status["latest_verified_baseline_label"]) >= 110
    assert int(current["candidate"]) >= 111
    assert history_110["external_review_status"] == "passed"
    assert history_110["external_verification_claimed"] is True
    assert history_109["status"] == "externally_verified_complete"
    assert history_109["baseline_archive"] == "ww-dps-simulator-2(109).zip"

    if "plan_sha256" in history_110:
        assert history_110["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert EXPECTED_PLAN_SHA256 == final_summary["plan_sha256"] == experiment_state["plan_sha256"]
    assert history_110["completed_guarded_checkpoint_count"] == 30 == provenance["trained_checkpoint_count"]
    assert history_110["requested_aggregate_ppo_budget"] == 300000 == provenance["requested_aggregate_timesteps"]
    assert history_110["actual_aggregate_sb3_model_timesteps"] == 307200 == provenance["actual_aggregate_model_timesteps"]
    assert provenance["failed_chunk_count"] == 0
    assert history_110["winner"] == "verified_bc_model" == best["winner_kind"] == final_summary["winner"]["winner_kind"]
    assert current["current_best_model"] == best["model_path"] == final_summary["winner"]["model_path"]
    _assert_close(current["current_best_result"], EXPECTED_BC_DAMAGE)
    _assert_close(best["total_damage"], EXPECTED_BC_DAMAGE)
    _assert_close(final_summary["winner"]["total_damage"], EXPECTED_BC_DAMAGE)

    assert current["global_optimum_claimed"] is False
    assert final_summary["global_optimum_proven"] is False
    assert final_summary["no_guarded_checkpoint_exceeded_bc"] is True
    assert current["route_similarity_objective"] is False
    assert final_summary["route_similarity_objective"] is False
    assert final_summary["route_similarity_usage"] == "diagnostic_only_not_used_for_winner_selection"
    assert current["manual_route_guidance"] is False
    assert current["bc_ppo_policy_guidance"] is False
    assert current["route_similarity_objective"] is False
    assert current["beam_search_long_execution"] is False
    assert current["mcts_execution"] is False
    assert (ROOT / "results/guarded_ppo_v109/final_experiment_summary.json").exists()
    assert (ROOT / "reports/guarded_ppo_experiment_v109_results.md").exists()

    assert [item["task"] for item in progress["next_planned_tasks"]][0] == "external review of candidate 113"
    assert "32GB low-memory Beam plan" in progress["next_planned_task"]
    print("project_progress_guarded_ppo_results_alignment_smoke_test ok")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert_close(actual: object, expected: float, *, tolerance: float = 1e-6) -> None:
    assert abs(float(actual) - expected) <= tolerance, (actual, expected)


if __name__ == "__main__":
    main()
