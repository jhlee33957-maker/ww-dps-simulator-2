from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    state = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    status = state["status"]
    assert status["latest_verified_baseline_label"] == "107"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2(107).zip"
    assert status["current_task"] == (
        "100000-step PPO continuation result ingestion, deterministic evaluation, "
        "and best-checkpoint comparison"
    )
    assert status["current_task_expected_next_archive"] == "108"
    assert status["candidate_expected_next_archive"] == "ww-dps-simulator-2-108.zip"

    current = state["current_in_progress_task"]
    assert current["candidate"] == "108"
    assert current["external_review_required"] is True
    assert current["external_verification_claimed"] is False
    assert current["latest_externally_verified_baseline"] == "107"
    assert current["full_bc_training_executed"] is True
    assert current["ppo_training_executed"] is True
    assert current["ppo_candidate_status"] == "valid_but_regressed"
    assert current["current_best_model"] == "models/maskable_ppo_bc_v105.zip"
    assert current["current_best_result"] == 5165134.682363356
    assert current["winner"] == "bc_model"
    assert current["winner_model"] == "models/maskable_ppo_bc_v105.zip"
    assert current["observation_version"] == "slot_generic_mechanics_v5"
    assert current["observation_shape"] == 314
    assert current["policy_action_count"] == 25
    assert current["max_policy_action_slots"] == 32
    assert current["source_route_file_sha256"] == "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a"
    assert current["dataset_sha256"] == "b020a1b9309b46bd87eb3fff4837aead53035c4c84620962f47feb9fc11846ff"
    assert current["action_data_hash"] == "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1"
    assert current["party_config_hash"] == "bd106ba1c0f5581436c35fea736a00fd6ad92b131f8b43ba8cf1e3dc89cbcb11"
    assert current["manifest_sha256"] == "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d"

    training = current["ppo_training"]
    assert training["source_bc_model"] == "models/maskable_ppo_bc_v105.zip"
    assert training["source_bc_model_sha256"] == "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e"
    assert training["ppo_model_path"] == "models/maskable_ppo_candidate_after_bc_v105.zip"
    assert training["ppo_model_sha256"] == "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513"
    assert training["timesteps"] == 100000
    assert training["seed"] == 42
    assert training["learning_rate"] == 0.0003
    assert training["entropy_coefficient"] == 0.01
    assert training["n_steps"] == 512
    assert training["batch_size"] == 64
    assert training["gamma"] == 0.999
    assert training["initial_active_character"] == "aemeath"
    assert training["curriculum_reset_mode"] == "none"
    assert training["elapsed_seconds"] == 321.1551833000267
    assert training["training_started_at"] == "2026-07-12T16:33:45.564697+00:00"
    assert training["training_finished_at"] == "2026-07-12T16:39:06.719900+00:00"

    evaluation = current["ppo_deterministic_evaluation"]
    assert evaluation["summary_path"] == "results/ppo_100k_evaluation_summary.json"
    assert evaluation["timeline_path"] == "results/ppo_100k_timeline.csv"
    assert evaluation["total_damage"] == 3600637.129626801
    assert evaluation["dps"] == 30005.309413556675
    assert evaluation["selected_action_count"] == 152
    assert evaluation["resolved_action_count"] == 152
    assert evaluation["selected_sequence_sha256"] == "0bba8688b3a085fde3a842901f659b24fdefd009102cc1ccba5a0d971a27c11d"
    assert evaluation["resolved_sequence_sha256"] == "9650b6e4d1b8f9ba616c26293f60c8cc4a5d6ea57dcf7153305aa085f84ad6e1"
    assert evaluation["manual_baseline_damage_ratio"] == 0.6971042094839032
    assert evaluation["manual_baseline_damage_delta"] == -1564497.5527365585
    assert evaluation["first_selected_action_divergence"] == {
        "zero_based_step": 4,
        "baseline": "aemeath_resonance_skill",
        "ppo": "swap_to_mornye",
    }

    history_108 = next(item for item in state["candidate_history"] if item["candidate"] == "108")
    assert history_108["status"] == "implemented_tests_passed_pending_external_review"
    assert history_108["external_review_status"] == "pending"
    assert history_108["external_verification_claimed"] is False
    assert history_108["full_bc_training_executed"] is True
    assert history_108["ppo_training_executed"] is True
    assert history_108["ppo_candidate_status"] == "valid_but_regressed"

    planned = state["next_planned_tasks"]
    assert planned[0]["task"] == "implement guarded PPO continuation with periodic deterministic evaluation and best-model retention"
    assert planned[0]["status"] == "after_candidate_108_external_verification"
    planned_text = json.dumps({"next_planned_task": state["next_planned_task"], "next_planned_tasks": planned})
    assert "100000-step PPO continuation from the verified BC model" not in planned_text
    assert "immediate unguarded PPO training" in planned_text
    assert "best-model retention" in planned_text
    print("project_progress_ppo_100k_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
