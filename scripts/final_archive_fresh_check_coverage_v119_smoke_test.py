from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manual_120s_bc_final_archive_integrity_smoke_test import (
    candidate_120_fresh_extraction_check_commands,
    candidate_119_fresh_extraction_check_commands,
    fresh_extraction_check_commands,
    legacy_fresh_extraction_check_commands,
)


HISTORY_AWARE_PROGRESS_TESTS = {
    "scripts/project_progress_transition_contract_v114_alignment_smoke_test.py",
    "scripts/project_progress_beam_v115_alignment_smoke_test.py",
    "scripts/project_progress_beam_completed_v116_alignment_smoke_test.py",
    "scripts/project_progress_mcts_v117_alignment_smoke_test.py",
    "scripts/project_progress_mcts_v118_alignment_smoke_test.py",
}

REQUIRED_COMMAND_PATHS = {
    "scripts/user_account_actual_v120_source_contract_smoke_test.py",
    "scripts/user_account_actual_v120_build_profiles_smoke_test.py",
    "scripts/user_account_actual_v120_weapon_loadout_smoke_test.py",
    "scripts/static_mist_r5_rank_resolution_smoke_test.py",
    "scripts/user_account_actual_v120_simulation_gate_smoke_test.py",
    "scripts/user_account_actual_v120_benchmark_immutability_smoke_test.py",
    "scripts/user_account_actual_v120_overlay_merge_smoke_test.py",
    "scripts/user_account_actual_v120_historical_party_hash_compatibility_smoke_test.py",
    "scripts/project_progress_user_account_v120_alignment_smoke_test.py",
    "scripts/mcts_v118_3x50k_integrity_smoke_test.py",
    "scripts/mcts_v118_3x50k_winner_replay_parity_smoke_test.py",
    "scripts/mcts_result_role_reporting_smoke_test.py",
    "scripts/mcts_v118_production_cleanup_smoke_test.py",
    "scripts/mcts_v118_seed_output_isolation_smoke_test.py",
    "scripts/mcts_v118_3x200_probe_smoke_test.py",
    "scripts/mcts_v118_3x200_probe_repeatability_smoke_test.py",
    "scripts/mcts_200_probe_smoke_test.py",
    "scripts/mcts_200_probe_repeatability_smoke_test.py",
    "scripts/beam_search_v116_completed_result_integrity_smoke_test.py",
    "scripts/beam_search_v114_streaming_spill_contract_smoke_test.py",
    "scripts/beam_search_lowmem_10000_probe_smoke_test.py",
    "scripts/beam_search_lowmem_10000_probe_repeatability_smoke_test.py",
    "scripts/transition_contract_v114_rebaseline_smoke_test.py",
    "scripts/transition_contract_v114_model_reevaluation_smoke_test.py",
    "scripts/full_real_cycle_integration_smoke_test.py",
    "scripts/direct_action_manifest_hash_guard_smoke_test.py",
    "scripts/final_archive_guarded_ppo_lightweight_suite.py",
    "scripts/final_archive_dataset_metadata_suite.py",
}


def command_paths(commands: list[list[str]]) -> set[str]:
    return {command[1].replace("\\", "/") for command in commands}


def assert_full_coverage(commands: list[list[str]]) -> None:
    candidate_120 = candidate_120_fresh_extraction_check_commands()
    candidate_119 = candidate_119_fresh_extraction_check_commands()
    legacy = legacy_fresh_extraction_check_commands()
    normalized = [tuple(command[1:]) for command in commands]
    assert len(commands) > 9
    assert len(normalized) == len(set(normalized)), "duplicate fresh-extraction command"
    assert set(map(tuple, candidate_120)).issubset(set(map(tuple, commands)))
    assert set(map(tuple, candidate_119)).issubset(set(map(tuple, commands)))
    assert set(map(tuple, legacy)).issubset(set(map(tuple, commands)))
    paths = command_paths(commands)
    assert REQUIRED_COMMAND_PATHS.issubset(paths)
    assert HISTORY_AWARE_PROGRESS_TESTS.issubset(paths)


def main() -> None:
    commands = fresh_extraction_check_commands()
    candidate_120 = candidate_120_fresh_extraction_check_commands()
    candidate_119 = candidate_119_fresh_extraction_check_commands()
    legacy = legacy_fresh_extraction_check_commands()
    assert commands == candidate_120 + candidate_119 + legacy
    assert_full_coverage(commands)
    try:
        assert_full_coverage(candidate_119 + legacy)
    except AssertionError:
        pass
    else:
        raise AssertionError("coverage guard accepted a checker missing candidate-120 commands")
    try:
        assert_full_coverage(candidate_120)
    except AssertionError:
        pass
    else:
        raise AssertionError("coverage guard accepted a candidate-120-only checker mutation")
    print(
        "final_archive_fresh_check_coverage_v119_smoke_test ok "
        f"candidate_120={len(candidate_120)} candidate_119={len(candidate_119)} "
        f"legacy={len(legacy)} total={len(commands)} mutation_rejected=true"
    )


if __name__ == "__main__":
    main()
