from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.demo_contract import party_config_hash


TRANSITION_SHA256 = "210538d4bf99789d0af08ecff5fb76dc3f472f5b170a144d9f1b3b1f46116b9c"
PARTY_CONFIG_HASH = "baff722d9ce79cf7f57891c439b7b3fd746ad76e779e4d582eaa51802eba2684"


def read_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8-sig"))


def main() -> None:
    progress = read_json("PROJECT_PROGRESS_STATE.json")
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "123"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-123(3).zip"
    assert status["latest_verified_archive_sha256"] == (
        "2d6c396df09645c4a304acebffea88d41555a6de05ed41d6ee7867648a5712f8"
    )
    assert status["current_candidate"] == "124"
    assert status["current_candidate_stage"] == "timing-core-2d-b1-lynae-polychrome-leap-stage2"
    assert status["current_task_status"] == "candidate_pending_external_review"
    assert status["do_not_treat_current_task_as_complete_until_reviewed"] is True

    transition_path = ROOT / "data/transition_config.json"
    transition = read_json("data/transition_config.json")
    plan = read_json("data/beam_search_plan_v114_32gb.json")
    historical_summary = read_json("results/manual_120s_baseline_v114_summary.json")
    historical_contract = plan["transition_contract"]
    assert plan["candidate"] == 114 and historical_contract["version"] == "v114"
    assert historical_contract["generic_swap_action_time"] == 0.0
    assert historical_contract["generic_swap_combat_time_cost"] == 0.0
    assert historical_contract["swap_reentry_cooldown_clock"] == "combat_time"
    assert transition["generic_swap_fallback"]["reentry_cooldown_clock"] == "combat_time"
    assert hashlib.sha256(transition_path.read_bytes()).hexdigest() == TRANSITION_SHA256
    assert plan["data_contract_hashes"]["transition_config_sha256"] == TRANSITION_SHA256
    assert plan["data_contract_hashes"]["party_config_hash"] == PARTY_CONFIG_HASH
    assert party_config_hash(root=ROOT) == PARTY_CONFIG_HASH
    runtime_contract = historical_summary["runtime_contract"]
    assert runtime_contract["transition_contract_version"] == "v114"
    assert runtime_contract["observation_version"] == "slot_generic_mechanics_v5"
    assert runtime_contract["observation_shape"] == 314
    assert runtime_contract["policy_action_count"] == 25

    stage = progress["candidate_124_timing_core_1"]
    assert stage["effective_candidate_124_swap_reentry_clock"] == "current_time"
    assert stage["effective_swap_reentry_clock_source"] == "candidate_124_timing_runtime_override"
    assert stage["historical_transition_config_clock"] == "combat_time"
    assert stage["historical_transition_config_sha256"] == TRANSITION_SHA256
    assert stage["historical_party_config_hash"] == PARTY_CONFIG_HASH
    assert stage["historical_base_config_modified"] is False
    assert stage["observation_v7_required"] is True
    assert stage["training_allowed_after_timing_patch"] is False
    assert stage["search_allowed_after_timing_patch"] is False
    assert stage["historical_results_status"] == "preserved_but_requires_timing_rebaseline"
    print("project_progress_transition_contract_v114_alignment_smoke_test ok historical=combat_time effective=current_time")


if __name__ == "__main__":
    main()
