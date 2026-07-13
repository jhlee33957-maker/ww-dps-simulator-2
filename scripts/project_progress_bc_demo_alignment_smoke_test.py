from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    data = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    assert int(data["status"]["latest_verified_baseline_label"]) >= 107
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
    history_106 = next(item for item in data["candidate_history"] if item["candidate"] == "106")
    assert history_106["status"] == "externally_verified_complete"
    assert history_106["external_review_status"] == "passed"
    assert history_106["external_verification_label"] == "106"
    assert history_106["baseline_archive"] == "ww-dps-simulator-2(106).zip"
    assert history_106["external_verification_claimed"] is True
    assert history_106["full_bc_training_executed"] is False
    history_107 = next(item for item in data["candidate_history"] if item["candidate"] == "107")
    assert history_107["status"] == "externally_verified_complete"
    assert history_107["external_review_status"] == "passed"
    assert history_107["external_verification_label"] == "107"
    assert history_107["baseline_archive"] == "ww-dps-simulator-2(107).zip"
    assert history_107["external_verification_claimed"] is True
    assert history_107["full_bc_training_executed"] is True
    assert history_107["ppo_training_executed"] is False
    milestone_107 = next(item for item in data["completed_milestones"] if item.get("id") == "M017")
    assert milestone_107["status"] == "externally_verified_complete"
    assert milestone_107["external_verification_label"] == "107"
    assert milestone_107["model_path"] == "models/maskable_ppo_bc_v105.zip"
    assert milestone_107["model_sha256"] == "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e"
    assert milestone_107["selected_sequence_sha256"] == "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
    assert milestone_107["resolved_sequence_sha256"] == "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
    print("project_progress_bc_demo_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
