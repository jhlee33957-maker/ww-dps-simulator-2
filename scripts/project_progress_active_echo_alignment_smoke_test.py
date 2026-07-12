from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = data["status"]
    assert status["latest_verified_archive"] == "ww-dps-simulator-2(104).zip"
    assert status["latest_verified_baseline_label"] == "104"
    assert status["current_task"] == "120-second deterministic manual baseline"
    assert status["current_task_status"] == "implemented_tests_passed_pending_external_review"
    assert status["do_not_treat_current_task_as_complete_until_reviewed"] is True

    assert data["next_planned_task"] == "external review of manual baseline candidate 105, then BC demonstration regeneration and PPO retraining"
    planned = data["next_planned_tasks"]
    assert [item["task"] for item in planned[:4]] == [
        "external review of manual baseline candidate 105",
        "BC/PPO regeneration",
        "Beam Search/MCTS comparison",
        "source-resolution follow-ups",
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

    full_cycle = next(item for item in data["completed_milestones"] if item["id"] == "M014")
    assert full_cycle["status"] == "externally_verified_complete"
    assert full_cycle["candidate"] == "104"
    assert full_cycle["final_combat_frames"] == 1977
    assert full_cycle["placeholder_fallback_count"] == 1
    assert full_cycle["state_injection_used"] is False
    assert full_cycle["all_selected_actions_available"] is True
    assert full_cycle["policy_action_count"] == 25
    assert full_cycle["observation_version"] == "slot_generic_mechanics_v5"
    assert full_cycle["observation_shape"] == 314
    assert full_cycle["max_policy_action_slots"] == 32
    print("project_progress_active_echo_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
