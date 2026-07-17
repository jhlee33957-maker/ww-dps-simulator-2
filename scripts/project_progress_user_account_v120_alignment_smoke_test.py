from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "119"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-119(1).zip"
    assert status["latest_verified_archive_sha256"] == "7248290f4b3f3f8107cfd10ff1b5e539167721b19a182fdb69b875221ce394ae"
    assert status["current_candidate"] == "120"
    assert status["current_task_status"] == "candidate_pending_external_review"
    assert status["candidate_expected_next_archive"] == "ww-dps-simulator-2-120.zip"

    current = progress["current_in_progress_task"]
    assert current["candidate"] == "120"
    assert current["external_verification_claimed"] is False
    assert current["account_profiles_stored"] is True
    assert current["account_weapon_loadouts_stored"] is True
    assert current["account_constellation_mechanics_implemented"] is False
    assert current["account_simulation_ready"] is False
    assert current["account_manual_baseline_executed"] is False
    assert current["account_bc_demonstration_regenerated"] is False
    assert current["account_bc_ppo_training_executed"] is False
    assert current["account_ppo_evaluation_executed"] is False
    assert current["account_beam_search_executed"] is False
    assert current["account_mcts_search_executed"] is False
    assert current["global_optimum_claimed"] is False
    assert current["account_build_profile_overlay_path"] == "data/account_build_profiles_v120.json"
    assert current["account_build_profile_overlay_sha256"] == (
        "a195de7f2ee505613685e15bcc673692dbc5704bd94df05171a52536ba96a789"
    )
    assert current["account_weapon_extension_overlay_path"] == "data/account_weapon_extensions_v120.json"
    assert current["account_weapon_extension_overlay_sha256"] == (
        "f3858c8c2a038662d270ae48c51e1cc793a5d757e9f1b9d5cb18b7edb0443390"
    )
    assert current["base_build_profiles_sha256"] == (
        "fe0e46aaddb818ecd9b0180b3aa955671328a03c179e9dd5f8b9a7fc85506aa7"
    )
    assert current["base_weapons_sha256"] == "1e5595c9c9cb1b300d5f0e21b1f493b527f2868503511b6c1c467209b3c8df33"
    assert current["historical_party_config_hash_preserved"] == (
        "baff722d9ce79cf7f57891c439b7b3fd746ad76e779e4d582eaa51802eba2684"
    )
    assert current["account_sequences"] == {"aemeath": 6, "lynae": 2, "mornye": 3}
    assert current["account_profile_ids"] == {
        "aemeath": "aemeath_account_actual_01",
        "lynae": "lynae_account_actual_01",
        "mornye": "mornye_account_actual_01",
    }
    assert current["account_weapons"] == {
        "aemeath": "Everbright Polestar R1",
        "lynae": "Static Mist R5",
        "mornye": "Starfield Calibrator R5",
    }
    assert current["existing_benchmark_mornye_weapon_remains"] == "Discord R5"
    assert current["existing_benchmark_profiles_preserved"] is True

    account = current["candidate_120_account_profiles"]
    contract_path = ROOT / account["source_contract_path"]
    assert contract_path.exists()
    assert hashlib.sha256(contract_path.read_bytes()).hexdigest() == account["source_contract_sha256"]
    build_overlay_path = ROOT / account["build_profile_overlay_path"]
    weapon_overlay_path = ROOT / account["weapon_extension_overlay_path"]
    assert build_overlay_path.exists()
    assert weapon_overlay_path.exists()
    assert hashlib.sha256(build_overlay_path.read_bytes()).hexdigest() == account["build_profile_overlay_sha256"]
    assert hashlib.sha256(weapon_overlay_path.read_bytes()).hexdigest() == account["weapon_extension_overlay_sha256"]
    assert account["base_build_profiles_sha256"] == (
        "fe0e46aaddb818ecd9b0180b3aa955671328a03c179e9dd5f8b9a7fc85506aa7"
    )
    assert account["base_weapons_sha256"] == "1e5595c9c9cb1b300d5f0e21b1f493b527f2868503511b6c1c467209b3c8df33"
    assert account["historical_party_config_hash_preserved"] == (
        "baff722d9ce79cf7f57891c439b7b3fd746ad76e779e4d582eaa51802eba2684"
    )
    assert account["simulation_status"] == "blocked_pending_constellation_mechanics"
    assert account["account_party_created"] is False
    assert account["account_result_created"] is False
    assert account["account_route_replay_executed"] is False
    assert account["beam_mcts_training_model_evaluation_executed"] is False
    assert account["profiles"]["aemeath_account_actual_01"]["sequence"] == 6
    assert account["profiles"]["lynae_account_actual_01"]["sequence"] == 2
    assert account["profiles"]["mornye_account_actual_01"]["sequence"] == 3

    assert progress["architecture_decisions"]["rl_observation"]["version"] == "slot_generic_mechanics_v5"
    assert progress["architecture_decisions"]["rl_observation"]["shape"] == 314
    assert current["observation_version"] == "slot_generic_mechanics_v5"
    assert current["observation_shape"] == 314
    assert current["policy_action_count"] == 25
    assert current["runtime_contract_hashes"]["direct_action_manifest_sha256"] == (
        "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d"
    )
    assert current["runtime_contract_hashes"]["action_data_hash"] == (
        "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1"
    )
    assert current["runtime_contract_hashes"]["transition_config_sha256"] == (
        "210538d4bf99789d0af08ecff5fb76dc3f472f5b170a144d9f1b3b1f46116b9c"
    )

    assert progress["candidate_history"][-1]["candidate"] == "120"
    assert progress["candidate_history"][-1]["status"] == "candidate_pending_external_review"
    print("project_progress_user_account_v120_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
