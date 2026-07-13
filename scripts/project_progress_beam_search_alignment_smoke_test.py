from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = progress["status"]
    current = progress["current_in_progress_task"]
    plan_sha = _sha256(ROOT / "data" / "beam_search_plan_v111.json")
    assert status["latest_verified_baseline_label"] == "110"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-110.zip"
    assert status["current_task_expected_next_archive"] == "111"
    assert current["candidate"] == "111"
    assert current["task"] == "independent deterministic diverse Beam Search infrastructure"
    assert current["beam_search_long_execution"] is False
    assert current["mcts_execution"] is False
    assert current["current_best_model"] == "models/maskable_ppo_bc_v105.zip"
    assert current["current_best_result"] == 5165134.682363356
    assert current["search_objective"] == "deterministic_120s_total_damage_only"
    assert current["manual_route_guidance"] is False
    assert current["bc_ppo_policy_guidance"] is False
    assert current["route_similarity_objective"] is False
    assert current["global_optimum_claimed"] is False
    assert current["plan_path"] == "data/beam_search_plan_v111.json"
    assert current["plan_sha256"] == plan_sha
    history_110 = next(item for item in progress["candidate_history"] if item["candidate"] == "110")
    assert history_110["status"] == "externally_verified_complete"
    history_111 = next(item for item in progress["candidate_history"] if item["candidate"] == "111")
    assert history_111["status"] == "implemented_tests_passed_pending_external_review"
    assert [item["task"] for item in progress["next_planned_tasks"]] == [
        "external review of candidate 111",
        "run the 30-second Beam Search calibration stage",
        "review expansion rate, memory, diversity, and pruning diagnostics",
        "run the 120-second full Beam Search stage only after calibration review",
        "compare the best search route against manual, BC, and all PPO checkpoints",
        "use MCTS only if Beam Search coverage is inadequate or excessively myopic",
    ]
    print("project_progress_beam_search_alignment_smoke_test ok")


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
