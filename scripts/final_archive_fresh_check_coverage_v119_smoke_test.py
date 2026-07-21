from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manual_120s_bc_final_archive_integrity_smoke_test import (
    candidate_124_fresh_extraction_check_commands,
    candidate_123_fresh_extraction_check_commands,
    candidate_122_fresh_extraction_check_commands,
    candidate_121_fresh_extraction_check_commands,
    candidate_120_fresh_extraction_check_commands,
    candidate_119_fresh_extraction_check_commands,
    fresh_extraction_check_commands,
    legacy_fresh_extraction_check_commands,
)


HISTORY_AWARE_PROGRESS_TESTS = {
    "scripts/project_progress_timing_core_v124_alignment_smoke_test.py",
    "scripts/project_progress_timing_core_stage2a_v124_alignment_smoke_test.py",
    "scripts/project_progress_timing_core_stage2b_v124_alignment_smoke_test.py",
    "scripts/user_account_actual_v120_historical_party_hash_compatibility_smoke_test.py",
    "scripts/project_progress_transition_contract_v114_alignment_smoke_test.py",
    "scripts/scheduled_packet_chronological_interleaving_v124_smoke_test.py",
    "scripts/scheduled_packet_actual_processing_time_v124_smoke_test.py",
    "scripts/scheduled_packet_source_attribution_v124_smoke_test.py",
    "scripts/scheduled_packet_off_tune_ordering_v124_smoke_test.py",
    "scripts/lynae_vivid_packet_contract_v124_smoke_test.py",
    "scripts/lynae_vivid_immediate_swap_packet_persistence_v124_smoke_test.py",
    "scripts/lynae_vivid_payload_parity_v124_smoke_test.py",
    "scripts/lynae_vivid_source_attribution_no_duplicate_v124_smoke_test.py",
    "scripts/scheduled_packet_equal_timestamp_numeric_order_v124_smoke_test.py",
    "scripts/lynae_vivid_92f_source_order_invariance_v124_smoke_test.py",
    "scripts/project_progress_aemeath_runtime_fix_v123_alignment_smoke_test.py",
    "scripts/project_progress_account_party_v122_alignment_smoke_test.py",
    "scripts/project_progress_account_constellation_v121_alignment_smoke_test.py",
}

REQUIRED_COMMAND_PATHS = {
    "scripts/timing_markov_state_observation_audit_v124.py",
    "scripts/account_observation_v6_unchanged_v124_guard_smoke_test.py",
    "scripts/action_timing_contract_v124_backward_compatibility_smoke_test.py",
    "scripts/mornye_stage2c_source_ref_utf8_and_row_join_v124_smoke_test.py",
    "scripts/historical_results_timing_rebaseline_status_v124_smoke_test.py",
    "scripts/mcts_v118_3x50k_winner_replay_parity_smoke_test.py",
    "scripts/lynae_liberation_split_input_swap_v124_smoke_test.py",
    "scripts/lynae_vivid_early_swap_persistence_v124_smoke_test.py",
    "scripts/lynae_vivid_split_timing_v124_smoke_test.py",
    "scripts/mornye_liberation_timing_variant_schema_v124_smoke_test.py",
    "scripts/mornye_liberation_normal_timing_v124_smoke_test.py",
    "scripts/mornye_liberation_observation_timing_v124_smoke_test.py",
    "scripts/mornye_liberation_variant_selection_stability_v124_smoke_test.py",
    "scripts/mornye_liberation_payload_parity_v124_smoke_test.py",
    "scripts/mornye_liberation_zero_combat_time_v124_smoke_test.py",
    "scripts/mornye_liberation_no_duplicate_payload_v124_smoke_test.py",
    "scripts/mornye_basic_stage2_packet_contract_v124_smoke_test.py",
    "scripts/mornye_basic_stage2_tail_persistence_v124_smoke_test.py",
    "scripts/mornye_basic_stage2_payload_parity_v124_smoke_test.py",
    "scripts/mornye_basic_stage3_packet_contract_v124_smoke_test.py",
    "scripts/mornye_basic_stage3_tail_persistence_v124_smoke_test.py",
    "scripts/mornye_basic_stage3_payload_parity_v124_smoke_test.py",
    "scripts/mornye_basic_packet_swap_persistence_v124_smoke_test.py",
    "scripts/mornye_basic_packet_no_duplicate_payload_v124_smoke_test.py",
    "scripts/project_progress_timing_core_stage2b_v124_alignment_smoke_test.py",
    "scripts/mornye_stage2c_detachable_contract_v124_smoke_test.py",
    "scripts/mornye_heavy_inversion_s1_marker_exact_duration_v124_smoke_test.py",
    "scripts/mornye_heavy_inversion_payload_parity_v124_smoke_test.py",
    "scripts/mornye_heavy_inversion_no_duplicate_payload_v124_smoke_test.py",
    "scripts/mornye_distributed_array_frame1_heal_v124_smoke_test.py",
    "scripts/mornye_distributed_array_payload_parity_v124_smoke_test.py",
    "scripts/mornye_distributed_array_cast_trigger_independence_v124_smoke_test.py",
    "scripts/mornye_distributed_array_no_duplicate_payload_v124_smoke_test.py",
    "scripts/mornye_stage2c_prefix_readiness_v124_smoke_test.py",
    "scripts/project_progress_timing_core_stage2c_v124_alignment_smoke_test.py",
    "scripts/no_first_cycle_or_training_v124_smoke_test.py",
    "scripts/ongoing_action_instance_v124_smoke_test.py",
    "scripts/policy_action_order_v124_guard_smoke_test.py",
    "scripts/scheduled_packet_placeholder_v124_smoke_test.py",
    "scripts/swap_reentry_wall_clock_v124_smoke_test.py",
    "scripts/timing_markov_state_observation_audit_v124_smoke_test.py",
    "scripts/training_blocked_until_observation_audit_v124_smoke_test.py",
    "scripts/vivid_immediate_return_to_mornye_v124_smoke_test.py",
    "scripts/project_progress_timing_core_v124_alignment_smoke_test.py",
    "scripts/project_progress_timing_core_stage2a_v124_alignment_smoke_test.py",
    "scripts/aemeath_precombat_radiance_heavy_resolution_v123_smoke_test.py",
    "scripts/aemeath_precombat_radiance_consumption_v123_smoke_test.py",
    "scripts/aemeath_intro_starlume_acceleration_v123_smoke_test.py",
    "scripts/aemeath_starlume_liberation_bonus_v123_smoke_test.py",
    "scripts/aemeath_account_cycle_feasibility_v123_smoke_test.py",
    "scripts/aemeath_v123_policy_action_compatibility_smoke_test.py",
    "scripts/aemeath_v123_no_baseline_search_artifacts_smoke_test.py",
    "scripts/project_progress_aemeath_runtime_fix_v123_alignment_smoke_test.py",
    "scripts/account_party_overlay_v122_smoke_test.py",
    "scripts/account_party_v122_contract_smoke_test.py",
    "scripts/account_content_start_v122_smoke_test.py",
    "scripts/account_precombat_initial_state_v122_smoke_test.py",
    "scripts/account_party_v122_no_action_execution_smoke_test.py",
    "scripts/account_config_hash_v122_smoke_test.py",
    "scripts/account_party_v122_historical_hash_compatibility_smoke_test.py",
    "scripts/account_party_v122_ui_visibility_smoke_test.py",
    "scripts/project_progress_account_party_v122_alignment_smoke_test.py",
    "scripts/validate_account_party_v122.py",
    "scripts/user_account_constellation_v121_source_contract_smoke_test.py",
    "scripts/user_account_single_boss_scope_v121_smoke_test.py",
    "scripts/aemeath_s6_single_boss_v121_smoke_test.py",
    "scripts/aemeath_s1_precombat_v121_smoke_test.py",
    "scripts/aemeath_s2_sequential_hit_v121_smoke_test.py",
    "scripts/aemeath_s3_contributor_v121_smoke_test.py",
    "scripts/aemeath_s4_party_bonus_v121_smoke_test.py",
    "scripts/aemeath_s5_unsupported_v121_smoke_test.py",
    "scripts/aemeath_s6_fixed_crit_trajectory_v121_smoke_test.py",
    "scripts/lynae_s2_single_boss_v121_smoke_test.py",
    "scripts/lynae_s1_paint_precombat_v121_smoke_test.py",
    "scripts/lynae_s2_outro_early_end_v121_smoke_test.py",
    "scripts/mornye_s3_single_boss_v121_smoke_test.py",
    "scripts/mornye_s1_marker_v121_smoke_test.py",
    "scripts/mornye_s2_marker_crit_buildup_v121_smoke_test.py",
    "scripts/mornye_s3_starfield_independent_icd_v121_smoke_test.py",
    "scripts/account_constellation_observation_v6_smoke_test.py",
    "scripts/account_constellation_v121_benchmark_immutability_smoke_test.py",
    "scripts/account_constellation_v121_runtime_dispatch_smoke_test.py",
    "scripts/account_constellation_v121_real_action_damage_smoke_test.py",
    "scripts/account_constellation_v121_real_resource_state_smoke_test.py",
    "scripts/account_constellation_v121_real_buff_marker_smoke_test.py",
    "scripts/account_constellation_v121_real_timing_expiry_smoke_test.py",
    "scripts/account_constellation_v121_real_observation_smoke_test.py",
    "scripts/account_constellation_v121_action_id_mapping_smoke_test.py",
    "scripts/account_constellation_v121_source_audit_quality_smoke_test.py",
    "scripts/account_constellation_v121_damage_accounting_parity_smoke_test.py",
    "scripts/aemeath_s2_real_resolved_action_mapping_v121_smoke_test.py",
    "scripts/aemeath_s3_real_contributor_runtime_v121_smoke_test.py",
    "scripts/aemeath_s4_real_trigger_and_damage_v121_smoke_test.py",
    "scripts/aemeath_s6_authoritative_trajectory_fixed_crit_v121_smoke_test.py",
    "scripts/lynae_s2_first_action_and_outro_exact_v121_smoke_test.py",
    "scripts/mornye_s2_real_marker_crit_v121_smoke_test.py",
    "scripts/mornye_s2_field_lifetime_v121_smoke_test.py",
    "scripts/mornye_s3_starfield_no_duplicate_v121_smoke_test.py",
    "scripts/account_constellation_v121_authoritative_observation_smoke_test.py",
    "scripts/account_constellation_v121_source_audit_cell_parity_smoke_test.py",
    "scripts/aemeath_s2_direct_coefficient_real_v121_smoke_test.py",
    "scripts/aemeath_s2_mechanic_hit_sequence_real_v121_smoke_test.py",
    "scripts/aemeath_s2_fusion_packet_real_v121_smoke_test.py",
    "scripts/aemeath_s2_fusion_real_action_settlement_v121_smoke_test.py",
    "scripts/aemeath_s2_fusion_state_consumption_v121_smoke_test.py",
    "scripts/aemeath_s6_fusion_fixed_crit_real_v121_smoke_test.py",
    "scripts/aemeath_s2_actual_tune_packet_source_parity_v121_smoke_test.py",
    "scripts/aemeath_s2_tune_variant_5_vs_10_hits_v121_smoke_test.py",
    "scripts/aemeath_s2_tune_trajectory_consumption_v121_smoke_test.py",
    "scripts/aemeath_s2_fusion_final_damage_zone_v121_smoke_test.py",
    "scripts/aemeath_fusion_base_trigger_application_v121_smoke_test.py",
    "scripts/aemeath_fusion_per_source_icd_v121_smoke_test.py",
    "scripts/aemeath_fusion_in_combat_minimum_effect_v121_smoke_test.py",
    "scripts/aemeath_s3_fusion_heavy_application_v121_smoke_test.py",
    "scripts/aemeath_fusion_natural_state_settlement_v121_smoke_test.py",
    "scripts/aemeath_fusion_qte_application_v121_smoke_test.py",
    "scripts/aemeath_fusion_initial_combat_minimum_v121_smoke_test.py",
    "scripts/aemeath_fusion_first_action_order_v121_smoke_test.py",
    "scripts/aemeath_s3_fusion_heavy_source_cooldown_v121_smoke_test.py",
    "scripts/account_constellation_v121_metadata_runtime_alignment_smoke_test.py",
    "scripts/account_constellation_v121_current_runtime_metadata_strict_smoke_test.py",
    "scripts/account_constellation_v121_full_effect_mapping_completeness_smoke_test.py",
    "scripts/account_constellation_v121_no_row_only_source_refs_smoke_test.py",
    "scripts/aemeath_s3_direct_coefficients_real_v121_smoke_test.py",
    "scripts/aemeath_s3_crit_damage_runtime_v121_smoke_test.py",
    "scripts/aemeath_s3_exact_contributor_event_and_reset_v121_smoke_test.py",
    "scripts/aemeath_s3_charged_mode_effect_real_v121_smoke_test.py",
    "scripts/aemeath_s6_liberation_deepen_real_v121_smoke_test.py",
    "scripts/aemeath_s6_real_packet_fixed_crit_v121_smoke_test.py",
    "scripts/aemeath_s6_real_trajectory_gain_seraphic_v121_smoke_test.py",
    "scripts/aemeath_s6_party_response_gain_exact_v121_smoke_test.py",
    "scripts/aemeath_s6_starburst_fixed_crit_real_v121_smoke_test.py",
    "scripts/account_aemeath_explicit_mode_gate_v121_smoke_test.py",
    "scripts/account_aemeath_mode_completeness_gate_v121_smoke_test.py",
    "scripts/aemeath_s6_no_generic_trajectory_double_v121_smoke_test.py",
    "scripts/account_constellation_v121_source_range_sheet_parity_smoke_test.py",
    "scripts/candidate_121_bounded_import_portability_smoke_test.py",
    "scripts/account_constellation_v121_exact_source_traceability_smoke_test.py",
    "scripts/aemeath_s1_finale_prerequisite_real_v121_smoke_test.py",
    "scripts/lynae_s1_light_leap_real_v121_smoke_test.py",
    "scripts/lynae_s2_collective_interference_cap_real_v121_smoke_test.py",
    "scripts/account_constellation_v121_authoritative_trajectory_observation_smoke_test.py",
    "scripts/account_constellation_v121_full_source_mapping_smoke_test.py",
    "scripts/project_progress_account_constellation_v121_alignment_smoke_test.py",
    "scripts/user_account_actual_v120_source_contract_smoke_test.py",
    "scripts/user_account_actual_v120_build_profiles_smoke_test.py",
    "scripts/user_account_actual_v120_weapon_loadout_smoke_test.py",
    "scripts/static_mist_r5_rank_resolution_smoke_test.py",
    "scripts/user_account_actual_v120_simulation_gate_smoke_test.py",
    "scripts/user_account_actual_v120_benchmark_immutability_smoke_test.py",
    "scripts/user_account_actual_v120_overlay_merge_smoke_test.py",
    "scripts/mcts_v118_3x50k_integrity_smoke_test.py",
    "scripts/mcts_result_role_reporting_smoke_test.py",
    "scripts/mcts_v118_production_cleanup_smoke_test.py",
    "scripts/mcts_v118_seed_output_isolation_smoke_test.py",
    "scripts/mcts_v118_3x200_probe_smoke_test.py",
    "scripts/mcts_v118_3x200_probe_repeatability_smoke_test.py",
    "scripts/mcts_200_probe_smoke_test.py",
    "scripts/mcts_200_probe_repeatability_smoke_test.py",
    "scripts/beam_search_v116_completed_result_integrity_smoke_test.py",
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
    candidate_124 = candidate_124_fresh_extraction_check_commands()
    candidate_123 = candidate_123_fresh_extraction_check_commands()
    candidate_122 = candidate_122_fresh_extraction_check_commands()
    candidate_121 = candidate_121_fresh_extraction_check_commands()
    candidate_120 = candidate_120_fresh_extraction_check_commands()
    candidate_119 = candidate_119_fresh_extraction_check_commands()
    legacy = legacy_fresh_extraction_check_commands()
    normalized = [tuple(command[1:]) for command in commands]
    assert len(commands) > len(candidate_124)
    assert all(command in commands for command in candidate_124)
    assert all(command in commands for command in candidate_123)
    assert all(command in commands for command in candidate_122)
    assert len(normalized) == len(set(normalized)), "duplicate fresh-extraction command"
    assert set(map(tuple, candidate_121)).issubset(set(map(tuple, commands)))
    assert set(map(tuple, candidate_120)).issubset(set(map(tuple, commands)))
    assert set(map(tuple, candidate_119)).issubset(set(map(tuple, commands)))
    assert set(map(tuple, legacy)).issubset(set(map(tuple, commands)))
    paths = command_paths(commands)
    assert REQUIRED_COMMAND_PATHS.issubset(paths)
    assert HISTORY_AWARE_PROGRESS_TESTS.issubset(paths)


def main() -> None:
    commands = fresh_extraction_check_commands()
    candidate_124 = candidate_124_fresh_extraction_check_commands()
    candidate_123 = candidate_123_fresh_extraction_check_commands()
    candidate_122 = candidate_122_fresh_extraction_check_commands()
    candidate_121 = candidate_121_fresh_extraction_check_commands()
    candidate_120 = candidate_120_fresh_extraction_check_commands()
    candidate_119 = candidate_119_fresh_extraction_check_commands()
    legacy = legacy_fresh_extraction_check_commands()
    older = candidate_123 + candidate_122 + candidate_121 + candidate_120 + candidate_119 + legacy
    assert commands == candidate_124 + older
    assert len(candidate_124) == 55
    assert len(candidate_123) == 8
    assert len(candidate_122) == 10
    assert len(candidate_121) == 81
    assert len(candidate_120) == 8
    assert len(candidate_119) == 8
    assert len(legacy) == 83
    assert len(commands) == 253
    assert_full_coverage(commands)

    mutations = {
        "candidate-124 commands omitted": older,
        "candidate-124 audit generator omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/timing_markov_state_observation_audit_v124.py"
        ],
        "candidate-124 progress alignment omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/project_progress_timing_core_v124_alignment_smoke_test.py"
        ],
        "candidate-124 Stage-2A progress alignment omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/project_progress_timing_core_stage2a_v124_alignment_smoke_test.py"
        ],
        "candidate-124 Stage-2A behavior test omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/mornye_liberation_normal_timing_v124_smoke_test.py"
        ],
        "candidate-124 Stage-2B contract test omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/mornye_basic_stage2_packet_contract_v124_smoke_test.py"
        ],
        "candidate-124 Stage-2B progress alignment omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/project_progress_timing_core_stage2b_v124_alignment_smoke_test.py"
        ],
        "candidate-124 chronological interleaving omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/scheduled_packet_chronological_interleaving_v124_smoke_test.py"
        ],
        "candidate-124 actual processing time omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/scheduled_packet_actual_processing_time_v124_smoke_test.py"
        ],
        "candidate-124 source attribution omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/scheduled_packet_source_attribution_v124_smoke_test.py"
        ],
        "candidate-124 Off-Tune ordering omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/scheduled_packet_off_tune_ordering_v124_smoke_test.py"
        ],
        "historical party-config hash compatibility omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/user_account_actual_v120_historical_party_hash_compatibility_smoke_test.py"
        ],
        "historical v114 progress alignment omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/project_progress_transition_contract_v114_alignment_smoke_test.py"
        ],
        "candidate-123 progress regression omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/project_progress_aemeath_runtime_fix_v123_alignment_smoke_test.py"
        ],
        "MCTS v118 preserved-artifact guard omitted": [
            command for command in candidate_124 + older
            if command[1] != "scripts/mcts_v118_3x50k_winner_replay_parity_smoke_test.py"
        ],
        "candidate-123 and older coverage removed": candidate_124,
        "duplicate command introduced": commands + [commands[0]],
    }
    for label, mutation in mutations.items():
        try:
            assert_full_coverage(mutation)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"coverage guard accepted mutation: {label}")
    print(
        "final_archive_fresh_check_coverage_v119_smoke_test ok "
        f"candidate_124={len(candidate_124)} candidate_123={len(candidate_123)} candidate_122={len(candidate_122)} candidate_121={len(candidate_121)} candidate_120={len(candidate_120)} candidate_119={len(candidate_119)} "
        f"legacy={len(legacy)} total={len(commands)} mutations_rejected={len(mutations)}"
    )


if __name__ == "__main__":
    main()
