from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    assert int(data["status"]["latest_verified_baseline_label"]) >= 103

    active_echo = next(item for item in data["completed_milestones"] if item["id"] == "M013")
    assert active_echo["status"] == "complete"
    assert active_echo["baseline"] == "103"
    assert active_echo["archive"] == "ww-dps-simulator-2(103).zip"
    assert active_echo["verified_values"]["policy_action_count"] == 25
    assert active_echo["verified_values"]["observation_version"] == "slot_generic_mechanics_v5"
    assert active_echo["verified_values"]["observation_shape"] == 314

    u005 = next(item for item in data["known_unresolved_or_missing"] if item["id"] == "U005")
    assert u005["status"] == "externally_verified_complete_with_limits"
    note = u005["note"]
    assert "uncancelled 66F route" in note
    assert "Echo Off-Tune values are source-unconfirmed and runtime zero" in note
    assert "not_implemented" not in json.dumps(u005, ensure_ascii=False)

    full_cycle = next(item for item in data["completed_milestones"] if item["id"] == "M014")
    assert full_cycle["status"] == "externally_verified_complete"
    assert full_cycle["candidate"] == "104"
    assert full_cycle["latest_externally_verified_baseline"] == "104"
    assert full_cycle["final_combat_frames"] == 1977
    assert full_cycle["placeholder_fallback_count"] == 1
    assert full_cycle["state_injection_used"] is False
    assert full_cycle["all_selected_actions_available"] is True
    assert full_cycle["policy_action_count"] == 25
    assert full_cycle["observation_version"] == "slot_generic_mechanics_v5"
    assert full_cycle["observation_shape"] == 314
    assert full_cycle["max_policy_action_slots"] == 32
    milestone_text = json.dumps({"active_echo": active_echo, "full_cycle": full_cycle, "u005": u005}, ensure_ascii=False)
    assert "not_implemented" not in milestone_text
    assert "not implemented" not in milestone_text.lower()
    print("project_progress_active_echo_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
