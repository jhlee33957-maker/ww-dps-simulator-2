from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    data = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = data["status"]
    assert status["latest_verified_baseline_label"] == "105"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2(105).zip"
    assert status["current_task"] == "canonical BC demonstration regeneration and BC/PPO compatibility preflight"
    assert status["current_task_expected_next_archive"] == "106"
    assert status["candidate_expected_next_archive"] == "ww-dps-simulator-2(106).zip"
    current = data["current_in_progress_task"]
    assert current["candidate"] == "106"
    assert current["external_verification_claimed"] is False
    assert current["external_review_required"] is True
    assert current["observation_version"] == "slot_generic_mechanics_v5"
    assert current["observation_shape"] == 314
    assert current["policy_action_count"] == 25
    assert current["max_policy_action_slots"] == 32
    assert current["reward_formula"] == "damage_this_action / 10000.0"
    assert current["full_bc_training_executed"] is False
    assert current["ppo_training_executed"] is False
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
    assert "exact final ZIP validation completed" in current["final_archive_integrity"]
    assert current["external_verification_claimed"] is False
    assert current["final_archive_expected_cache_entry_count"] == 0
    assert current["final_archive_expected_raw_corrupted_sheet_occurrence_count"] == 0
    print("project_progress_bc_demo_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
