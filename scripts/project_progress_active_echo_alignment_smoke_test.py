from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = data["status"]
    assert status["latest_verified_archive"] == "ww-dps-simulator-2(103).zip"
    assert status["latest_verified_baseline_label"] == "103"
    assert status["current_task"] == "full real-cycle integration with active Echoes"
    assert status["current_task_status"] == "implemented_tests_passed_pending_external_review"
    assert status["do_not_treat_current_task_as_complete_until_reviewed"] is True

    assert data["next_planned_task"] == "external review of full-cycle candidate 104, then 120-second manual baseline"
    planned = data["next_planned_tasks"]
    assert [item["task"] for item in planned[:4]] == [
        "external review of full-cycle candidate 104",
        "120-second manual baseline",
        "BC/PPO regeneration",
        "Beam Search/MCTS comparison",
    ]
    planned_text = json.dumps(planned, ensure_ascii=False).lower()
    assert "active echo action implementation" not in planned_text
    assert "mornye and aemeath active echo action implementation" not in planned_text

    u005 = next(item for item in data["known_unresolved_or_missing"] if item["id"] == "U005")
    assert u005["status"] == "externally_verified_complete_with_limits"
    note = u005["note"]
    assert "uncancelled 66F route" in note
    assert "Echo Off-Tune values are source-unconfirmed and runtime zero" in note
    assert "not_implemented" not in json.dumps(u005, ensure_ascii=False)

    current = data["current_in_progress_task"]
    assert current["task"] == "full real-cycle integration with active Echoes"
    assert current["status"] == "implemented_tests_passed_pending_external_review"
    assert current["external_review_required"] is True
    assert current["external_verification_claimed"] is False
    assert current["latest_externally_verified_baseline"] == "103"
    assert current["candidate_expected_next_archive"] == "ww-dps-simulator-2(104).zip"
    assert current["final_combat_frames"] == 1977
    assert current["placeholder_fallback_count"] == 1
    assert current["state_injection_used"] is False
    assert current["all_selected_actions_available"] is True
    assert current["policy_action_count"] == 25
    assert current["observation_version"] == "slot_generic_mechanics_v5"
    assert current["observation_shape"] == 314
    assert current["max_policy_action_slots"] == 32
    print("project_progress_active_echo_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
