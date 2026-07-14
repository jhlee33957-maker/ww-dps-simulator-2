from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = progress["status"]
    current = progress["current_in_progress_task"]
    plan_sha = _sha256(ROOT / "data" / "beam_search_plan_v113_32gb.json")
    assert status["latest_verified_baseline_label"] == "112"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-112.zip"
    assert status["current_task_expected_next_archive"] == "113"
    assert current["candidate"] == "113"
    assert current["task"] == "32GB low-memory 120-second Beam Search plan and slim runtime workspace"
    assert current["beam_search_long_execution"] is False
    assert current["calibration_stage_executed"] is True
    assert current["full_search_stage_executed"] is False
    assert current["mcts_execution"] is False
    assert current["current_best_model"] == "models/maskable_ppo_bc_v105.zip"
    assert current["current_best_result"] == 5165134.682363356
    assert current["search_objective"] == "deterministic_120s_total_damage_only"
    assert current["manual_route_guidance"] is False
    assert current["bc_ppo_policy_guidance"] is False
    assert current["route_similarity_objective"] is False
    assert current["global_optimum_claimed"] is False
    assert current["plan_path"] == "data/beam_search_plan_v113_32gb.json"
    assert current["plan_sha256"] == plan_sha
    history_110 = next(item for item in progress["candidate_history"] if item["candidate"] == "110")
    assert history_110["status"] == "externally_verified_complete"
    history_111 = next(item for item in progress["candidate_history"] if item["candidate"] == "111")
    assert history_111["status"] == "externally_verified_complete"
    assert [item["task"] for item in progress["next_planned_tasks"]] == [
        "external review of candidate 113",
        "build the slim runtime workspace",
        "run the reviewed 32GB low-memory Beam plan to 3M expansions",
        "review memory, runtime, and best completed 120-second result",
        "resume to 5M only if useful, then run MCTS as an independent complementary search",
    ]
    print("project_progress_beam_search_alignment_smoke_test ok")


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
