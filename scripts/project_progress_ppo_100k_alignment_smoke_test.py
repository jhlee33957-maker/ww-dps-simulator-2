from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    state = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    history_108 = next(item for item in state["candidate_history"] if item["candidate"] == "108")
    assert history_108["task"] == (
        "100000-step PPO continuation result ingestion, deterministic evaluation, "
        "and best-checkpoint comparison"
    )
    assert history_108["status"] == "externally_verified_complete"
    assert history_108["external_review_status"] == "passed"
    assert history_108["external_verification_claimed"] is True
    assert history_108["external_verification_label"] == "108"
    assert history_108["baseline_archive"] == "ww-dps-simulator-2(108).zip"
    assert history_108["full_bc_training_executed"] is True
    assert history_108["ppo_training_executed"] is True
    assert history_108["ppo_candidate_status"] == "valid_but_regressed"
    assert history_108["ppo_model_path"] == "models/maskable_ppo_candidate_after_bc_v105.zip"
    assert history_108["ppo_model_sha256"] == "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513"
    assert history_108["ppo_total_damage"] == 3600637.129626801
    assert history_108["ppo_dps"] == 30005.309413556675
    assert history_108["winner"] == "bc_model"
    assert history_108["winner_model"] == "models/maskable_ppo_bc_v105.zip"
    assert history_108["current_best_result"] == 5165134.682363356
    assert history_108["comparison_artifact"] == "results/manual_bc_ppo_comparison_v108.json"
    assert history_108["archive_path"] == "../ww-dps-simulator-2(108).zip"
    print("project_progress_ppo_100k_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
