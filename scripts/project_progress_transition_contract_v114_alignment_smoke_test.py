from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    current = progress["current_in_progress_task"]
    assert status["latest_externally_verified_baseline"] == "120"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-120(1).zip"
    assert status["current_candidate"] == "121"
    assert current["candidate"] == "121"
    assert current["status"] == "candidate_pending_external_review"
    assert current["external_verification_claimed"] is False
    assert current["transition_contract_version"] == "v114"
    assert current["diagnostic_regression_correction"] == (
        "legacy placeholder warning leakage removed; unversioned transition foundation smoke test aligned with v114"
    )
    assert current["generic_swap"]["action_time"] == current["generic_swap"]["combat_time_cost"] == 0.0
    assert current["generic_swap"]["reentry_cooldown_clock"] == "combat_time"
    assert current["observation_version"] == "slot_generic_mechanics_v5"
    assert current["observation_shape"] == 314
    assert current["policy_action_count"] == 25
    assert current["plan_sha256"] == sha(ROOT / current["plan_path"])
    assert current["active_stage_id"] == "full_120s_lowmem_32gb_v114"
    assert current["accumulator_spill_format"] == "streaming_jsonl_gzip_v113"
    assert current["accumulator_spill_chunk_schema"] == "beam_search_accumulator_chunk_jsonl_gzip_v113"
    assert current["runtime_contract_hashes"]["transition_config_sha256"] == sha(ROOT / "data/transition_config.json")
    assert current["runtime_contract_hashes"]["buffs_sha256"] == sha(ROOT / "data/buffs.json")
    assert current["model_reevaluation_v114"]["manual_model_comparison_sha256"] == sha(
        ROOT / current["model_reevaluation_v114"]["manual_model_comparison_path"]
    )
    assert current["manual_v114"]["aemeath_outro_cast_count"] == 3
    assert current["manual_v114"]["aemeath_outro_upgrade_annotation_count"] == 3
    assert current["manual_v114"]["base_cast_and_upgrade_rows_disjoint"] is True
    assert current["model_reevaluation_v114"]["winner_aemeath_outro_cast_count"] == 3
    assert current["model_reevaluation_v114"]["winner_aemeath_outro_upgrade_annotation_count"] == 3
    probe = current["bounded_10000_probe"]
    assert probe["deterministic_result_sha256"] == "aa758e746344fbe685467540f16bdcc3c6899fdd6cb03e81ac881ce0440d92ef"
    assert probe["resolved_accumulator_spill_format"] == "streaming_jsonl_gzip_v113"
    assert probe["accumulator_spill_chunk_schema"] == "beam_search_accumulator_chunk_jsonl_gzip_v113"
    assert probe["two_isolated_process_repeatability_passed"] is True
    assert probe["repeat_spill_sha256s_identical"] is True
    assert probe["normal_process_exit"] is True
    assert probe["cleanup_completed"] is True
    assert probe["canonical_output_mutated"] is False
    assert current["interrupted_v113_beam_output"]["resume_allowed"] is False
    assert current["v114_3m_search_executed"] is True
    assert current["v114_3m_checkpoint_status"] == "superseded_by_completed_6p5m_resume"
    assert current["v114_completed_route_count"] == 128
    assert current["v114_checkpoint_resumable"] is True
    assert current["v114_5m_search_executed"] is False
    assert current["candidate_119_mcts"]["production_search_executed"] is True
    assert current["bc_training_executed"] is False
    assert current["ppo_training_executed"] is False
    assert current["global_optimum_claimed"] is False
    assert "reports/beam_search_v114_32gb_lowmem.md" in current["reports"]
    assert current["reactor_husk_unchanged"] == {
        "hit_frame": 49,
        "uncancelled_end_frame": 66,
        "action_time_seconds": 1.1,
    }
    print("project_progress_transition_contract_v114_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
