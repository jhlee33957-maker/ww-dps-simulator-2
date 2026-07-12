from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    data = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = data["status"]
    assert status["latest_verified_baseline_label"] == "106"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2(106).zip"
    assert status["current_task"] == "full BC warm-start artifact verification and deterministic evaluation reporting correction"
    assert status["current_task_expected_next_archive"] == "107"
    assert status["candidate_expected_next_archive"] == "ww-dps-simulator-2(107).zip"
    current = data["current_in_progress_task"]
    assert current["candidate"] == "107"
    assert current["external_verification_claimed"] is False
    assert current["external_review_required"] is True
    assert current["observation_version"] == "slot_generic_mechanics_v5"
    assert current["observation_shape"] == 314
    assert current["policy_action_count"] == 25
    assert current["max_policy_action_slots"] == 32
    assert current["full_bc_training_executed"] is True
    assert current["ppo_training_executed"] is False
    assert current["latest_externally_verified_baseline"] == "106"
    assert current["model_path"] == "models/maskable_ppo_bc_v105.zip"
    assert current["model_sha256"] == "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e"
    assert current["selected_action_count"] == 148
    assert current["resolved_action_count"] == 148
    assert current["manual_baseline_selected_sequence_match"] is True
    assert current["manual_baseline_resolved_sequence_match"] is True
    assert current["manual_baseline_character_damage_match"] is True
    assert current["model_metadata_mismatches"] == {}
    assert current["model_space_mismatches"] == {}
    manual = next(item for item in data["completed_milestones"] if item.get("id") == "M015")
    assert manual["status"] == "externally_verified_complete"
    assert manual["external_review_status"] == "externally_verified"
    assert manual["latest_externally_verified_baseline"] == "105"
    manual_cycle = data["manual_cycle_reference"]
    assert manual_cycle["status"] == "externally_verified_complete"
    assert manual_cycle["external_review_status"] == "externally_verified"
    assert manual_cycle["external_verification_label"] == "105"
    assert manual_cycle["latest_externally_verified_baseline"] == "105"
    assert "candidate_105_implemented_pending_external_review" not in json.dumps(manual_cycle, ensure_ascii=False)
    bc_demo = next(item for item in data["completed_milestones"] if item.get("id") == "M016")
    assert bc_demo["status"] == "externally_verified_complete"
    assert bc_demo["external_verification_label"] == "106"
    assert bc_demo["dataset_sha256"] == "b020a1b9309b46bd87eb3fff4837aead53035c4c84620962f47feb9fc11846ff"
    assert "pending exact candidate-107 ZIP validation" in current["final_archive_integrity"]
    assert current["external_verification_claimed"] is False
    history_106 = next(item for item in data["candidate_history"] if item["candidate"] == "106")
    assert history_106["status"] == "externally_verified_complete"
    assert history_106["external_review_status"] == "passed"
    assert history_106["external_verification_label"] == "106"
    assert history_106["baseline_archive"] == "ww-dps-simulator-2(106).zip"
    assert history_106["external_verification_claimed"] is True
    assert history_106["full_bc_training_executed"] is False
    history_107 = next(item for item in data["candidate_history"] if item["candidate"] == "107")
    assert history_107["status"] == "implemented_tests_passed_pending_external_review"
    assert history_107["external_review_status"] == "pending"
    assert history_107["external_verification_claimed"] is False
    assert history_107["full_bc_training_executed"] is True
    assert history_107["ppo_training_executed"] is False
    planned = data["next_planned_tasks"]
    assert planned[0]["task"] == "external review of candidate 107 deterministic BC evaluation reporting correction"
    assert planned[0]["status"] == "current"
    assert planned[1]["task"] == "100000-step PPO continuation from the verified BC model"
    assert planned[1]["status"] == "after_candidate_107_external_verification"
    assert planned[1]["model_source"] == "models/maskable_ppo_bc_v105.zip"
    assert planned[1]["initial_active_character"] == "aemeath"
    assert planned[1]["reset_mode"] == "none"
    assert planned[2]["task"] == "deterministic normal-reset evaluation of the PPO candidate"
    assert planned[2]["status"] == "after_ppo_100k"
    assert planned[3]["task"] == "compare manual baseline, BC model, and PPO result before any additional PPO/search budget"
    assert planned[3]["status"] == "after_ppo_evaluation"
    assert (
        data["next_planned_task"]
        == "external review of candidate 107 deterministic BC evaluation reporting correction; after external verification run 100000-step PPO continuation from the verified BC model"
    )
    planned_text = json.dumps({"next_planned_task": data["next_planned_task"], "next_planned_tasks": planned}, ensure_ascii=False)
    future_planned_text = json.dumps(planned[1:], ensure_ascii=False)
    assert "candidate 106" not in planned_text
    assert "user-run full BC" not in planned_text
    assert "full BC warm-start" not in planned_text
    assert "deterministic BC evaluation" not in future_planned_text
    print("project_progress_bc_demo_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
