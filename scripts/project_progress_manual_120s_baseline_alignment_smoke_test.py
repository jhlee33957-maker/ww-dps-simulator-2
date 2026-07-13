from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    state = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    assert int(state["status"]["latest_verified_baseline_label"]) >= 105

    manual = next(item for item in state["completed_milestones"] if item["id"] == "M015")
    assert manual["status"] == "externally_verified_complete"
    assert manual["external_review_status"] == "externally_verified"
    assert manual["candidate"] == "105"
    assert manual["external_verification_label"] == "105"
    assert manual["latest_externally_verified_baseline"] == "105"
    primary = manual["manual_120s_baseline"]["primary"]
    assert primary["final_combat_time"] == 120.0
    assert primary["total_damage"] == 5165134.682363359
    assert primary["selected_sequence_sha256"] == "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
    assert primary["resolved_sequence_sha256"] == "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
    assert manual["route_json"] == "data/manual_120s_baseline_routes_v104.json"
    assert manual["result_json"] == "results/manual_120s_baseline_v104_summary.json"
    assert manual["timeline_csv"] == "results/manual_120s_baseline_v104_timeline.csv"
    assert manual["report"] == "reports/manual_120s_baseline_v104.md"

    manual_cycle = state["manual_cycle_reference"]
    assert manual_cycle["status"] == "externally_verified_complete"
    assert manual_cycle["external_review_status"] == "externally_verified"
    assert manual_cycle["external_verification_label"] == "105"
    assert manual_cycle["latest_externally_verified_baseline"] == "105"
    assert manual_cycle["primary_total_damage"] == 5165134.682363359
    assert manual_cycle["primary_dps"] == 43042.78901969466
    assert manual_cycle["primary_route_hash"] == "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
    artifacts = manual_cycle["artifacts"]
    assert artifacts["route_json"] == "data/manual_120s_baseline_routes_v104.json"
    assert artifacts["summary_json"] == "results/manual_120s_baseline_v104_summary.json"
    assert artifacts["timeline_csv"] == "results/manual_120s_baseline_v104_timeline.csv"
    assert artifacts["report"] == "reports/manual_120s_baseline_v104.md"

    u007 = next(item for item in state["known_unresolved_or_missing"] if item["id"] == "U007")
    assert u007["status"] == "externally_verified_complete"
    assert "verified as baseline 105" in u007["note"]
    assert "not built yet" not in u007["note"]
    assert "candidate 104 pending external review" not in u007["note"]
    milestone_text = json.dumps(
        {
            "manual": manual,
            "manual_cycle": manual_cycle,
            "known": state["known_unresolved_or_missing"],
        },
        ensure_ascii=False,
    )
    assert "120-second manual baseline remains" not in milestone_text
    assert "not built yet" not in milestone_text
    assert "candidate 104 pending external review" not in milestone_text
    print("project_progress_manual_120s_baseline_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
