from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    state = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = state["status"]
    assert status["latest_verified_baseline_label"] == "105"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2(105).zip"
    assert status["current_task"] == "canonical BC demonstration regeneration and BC/PPO compatibility preflight"
    assert status["candidate_expected_next_archive"] == "ww-dps-simulator-2(106).zip"
    assert status["current_task_status"] == "implemented_tests_passed_pending_external_review"
    current = state["current_in_progress_task"]
    assert current["task"] == "canonical BC demonstration regeneration and BC/PPO compatibility preflight"
    assert current["candidate"] == "106"
    assert current["external_verification_claimed"] is False
    assert current["latest_externally_verified_baseline"] == "105"
    assert current["final_combat_time"] == 120.0
    u007 = next(item for item in state["known_unresolved_or_missing"] if item["id"] == "U007")
    assert u007["status"] == "externally_verified_complete"
    assert "verified as baseline 105" in u007["note"]
    assert "not built yet" not in u007["note"]
    assert "candidate 104 pending external review" not in u007["note"]
    current_text = json.dumps(
        {
            "status": state["status"],
            "current": current,
            "known": state["known_unresolved_or_missing"],
            "next": state["next_planned_tasks"],
        },
        ensure_ascii=False,
    )
    assert "120-second manual baseline remains" not in current_text
    assert "not built yet" not in current_text
    print("project_progress_manual_120s_baseline_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
