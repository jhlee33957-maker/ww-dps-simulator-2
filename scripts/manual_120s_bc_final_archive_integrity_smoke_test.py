from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEMO_PATH = ROOT / "data" / "generated" / "manual_120s_bc_demonstration_v105.npz"
DIRECT_ACTION_MANIFEST_SHA256 = "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d"
SOURCE_ROUTE_FILE_SHA256 = "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a"


DEFAULT_ARCHIVE = ROOT.parent / "ww-dps-simulator-2-119.zip"
EXPECTED_BC_MODEL_SHA256 = "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e"
EXPECTED_PPO_MODEL_SHA256 = "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513"
EXPECTED_EVAL_SELECTED_SEQUENCE_SHA256 = "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
EXPECTED_EVAL_RESOLVED_SEQUENCE_SHA256 = "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
EXPECTED_EVAL_TOTAL_DAMAGE = 5165134.682363356
EXPECTED_EVAL_DPS = 43042.78901969464
EXPECTED_SCHEDULED_DAMAGE = 205987.4042873791
EXPECTED_DAMAGE_BY_CHARACTER = {
    "aemeath": 3733934.8538652016,
    "mornye": 268807.92005964793,
    "lynae": 1162391.9084385103,
}
EXPECTED_PPO_SELECTED_SEQUENCE_SHA256 = "0bba8688b3a085fde3a842901f659b24fdefd009102cc1ccba5a0d971a27c11d"
EXPECTED_PPO_RESOLVED_SEQUENCE_SHA256 = "9650b6e4d1b8f9ba616c26293f60c8cc4a5d6ea57dcf7153305aa085f84ad6e1"
EXPECTED_PPO_TOTAL_DAMAGE = 3600637.129626801
EXPECTED_PPO_DPS = 30005.309413556675
EXPECTED_PPO_SCHEDULED_DAMAGE = 140026.5111366104
EXPECTED_BEAM_PLAN_SHA256 = "b504def4e0c1da82ef2a6024d19ccac76fe175df51899e50d12f3bff99a17998"
EXPECTED_LOWMEM_BEAM_PLAN_SHA256 = "ffd9ce47ec9b92b2c4b59f295d50d0ce5204fcba577af0f78b9fa917b19b291d"
EXPECTED_V114_BEAM_PLAN_SHA256 = "e70826d0040444f834398d55c922aacb4ee5b484bc6ef2e75ca5a0ad603bc18c"
EXPECTED_V114_TRANSITION_CONFIG_SHA256 = "210538d4bf99789d0af08ecff5fb76dc3f472f5b170a144d9f1b3b1f46116b9c"
EXPECTED_V114_BUFFS_SHA256 = "fe8b8fc63e8b9a3405a61ebe08a2cafa13f94dd4af91d1670b968df727cb554d"
EXPECTED_PPO_DAMAGE_BY_CHARACTER = {
    "aemeath": 2674131.053725695,
    "mornye": 201528.93426401448,
    "lynae": 724977.1416370921,
}
REQUIRED_FILES = (
    "PROJECT_PROGRESS_STATE.json",
    "data/mcts_plan_v117_32gb.json",
    "reports/mcts_v117_32gb_design.md",
    "search/search_state_codec.py",
    "search/mcts_plan.py",
    "search/mcts_state.py",
    "search/mcts_tree.py",
    "search/mcts_checkpoint.py",
    "search/mcts_search.py",
    "search/mcts_reporting.py",
    "search/run_mcts.py",
    "scripts/mcts_plan_v117_32gb_contract_smoke_test.py",
    "scripts/mcts_search_independence_smoke_test.py",
    "scripts/mcts_state_clone_behavioral_parity_smoke_test.py",
    "scripts/mcts_lightweight_action_execution_parity_smoke_test.py",
    "scripts/mcts_lightweight_rollout_state_parity_smoke_test.py",
    "scripts/mcts_snapshot_reconstruction_smoke_test.py",
    "scripts/mcts_uct_progressive_widening_smoke_test.py",
    "scripts/mcts_mast_rollout_determinism_smoke_test.py",
    "scripts/mcts_action_mask_zero_time_loop_guard_smoke_test.py",
    "scripts/mcts_selection_guard_test_support.py",
    "scripts/mcts_selection_action_limit_smoke_test.py",
    "scripts/mcts_selection_zero_time_limit_smoke_test.py",
    "scripts/mcts_no_legal_tree_node_smoke_test.py",
    "scripts/mcts_checkpoint_resume_equivalence_smoke_test.py",
    "scripts/mcts_checkpoint_corruption_no_mutation_smoke_test.py",
    "scripts/mcts_previous_checkpoint_fallback_smoke_test.py",
    "scripts/mcts_memory_budget_guard_smoke_test.py",
    "scripts/mcts_output_root_isolation_smoke_test.py",
    "scripts/mcts_completed_route_replay_parity_smoke_test.py",
    "scripts/mcts_v117_test_utils.py",
    "scripts/mcts_probe_worker_v117.py",
    "scripts/mcts_200_probe_smoke_test.py",
    "scripts/mcts_200_probe_repeatability_smoke_test.py",
    "scripts/mcts_reporting_current_winner_smoke_test.py",
    "scripts/project_progress_mcts_v117_alignment_smoke_test.py",
    "data/manual_120s_baseline_routes_v104.json",
    "data/generated/manual_120s_bc_demonstration_v105.npz",
    "results/manual_120s_bc_demonstration_v105_summary.json",
    "results/ppo_evaluation_summary.json",
    "results/ppo_timeline.csv",
    "results/ppo_100k_evaluation_summary.json",
    "results/ppo_100k_timeline.csv",
    "results/manual_bc_ppo_comparison_v108.json",
    "results/training_metadata.json",
    "data/guarded_ppo_experiment_plan_v109.json",
    "results/guarded_ppo_v109/experiment_state.json",
    "results/guarded_ppo_v109/leaderboard.json",
    "results/guarded_ppo_v109/best_checkpoint.json",
    "results/guarded_ppo_v109/final_experiment_summary.json",
    "reports/manual_120s_bc_demonstration_v105.md",
    "reports/guarded_ppo_experiment_v109.md",
    "reports/guarded_ppo_experiment_v109_results.md",
    "reports/beam_search_v111.md",
    "reports/beam_search_v111_calibration_results.md",
    "data/beam_search_plan_v111.json",
    "data/beam_search_plan_v113_32gb.json",
    "reports/beam_search_v113_32gb_lowmem.md",
    "results/runtime_cleanup_v113_receipt.json",
    "results/beam_search_v111/execution_result.json",
    "results/beam_search_v111/search_state.json",
    "results/beam_search_v111/leaderboard.json",
    "results/beam_search_v111/best_route.json",
    "results/beam_search_v111/final_summary.json",
    "results/beam_search_v111/calibration_result_summary.json",
    "models/maskable_ppo_bc_v105.zip",
    "models/maskable_ppo_bc_v105.zip.bc_metadata.json",
    "models/maskable_ppo_candidate_after_bc_v105.zip",
    "models/maskable_ppo_candidate_after_bc_v105.zip.ppo_metadata.json",
    "rl/damage_attribution.py",
    "rl/demo_contract.py",
    "rl/evaluation_report.py",
    "rl/evaluate_maskable_ppo.py",
    "rl/guarded_ppo.py",
    "rl/run_guarded_ppo_experiment.py",
    "rl/train_maskable_ppo.py",
    "rl/pretrain_maskable_ppo_bc.py",
    "search/__init__.py",
    "search/beam_plan.py",
    "search/beam_resume_extension.py",
    "search/beam_reporting.py",
    "search/beam_spill.py",
    "search/beam_search.py",
    "search/beam_state.py",
    "search/run_beam_search.py",
    "scripts/manual_120s_bc_demo_contract_smoke_test.py",
    "scripts/manual_120s_bc_packaged_generation_parity_smoke_test.py",
    "scripts/manual_120s_bc_report_portability_smoke_test.py",
    "scripts/bc_pretrain_evaluator_contract_smoke_test.py",
    "scripts/evaluate_bc_sidecar_compatibility_smoke_test.py",
    "scripts/pretrain_bc_initial_active_contract_smoke_test.py",
    "scripts/project_progress_active_echo_alignment_smoke_test.py",
    "scripts/project_progress_manual_120s_baseline_alignment_smoke_test.py",
    "scripts/project_progress_bc_demo_alignment_smoke_test.py",
    "scripts/project_progress_ppo_100k_alignment_smoke_test.py",
    "scripts/project_progress_guarded_ppo_alignment_smoke_test.py",
    "scripts/project_progress_guarded_ppo_results_alignment_smoke_test.py",
    "scripts/evaluation_event_source_damage_attribution_smoke_test.py",
    "scripts/evaluation_scheduled_damage_role_breakdown_smoke_test.py",
    "scripts/bc_evaluation_manual_baseline_parity_smoke_test.py",
    "scripts/ppo_100k_evaluation_contract_smoke_test.py",
    "scripts/manual_bc_ppo_comparison_smoke_test.py",
    "scripts/ingest_guarded_ppo_v109_completed_experiment.py",
    "scripts/guarded_ppo_plan_contract_smoke_test.py",
    "scripts/guarded_ppo_branch_continuation_smoke_test.py",
    "scripts/guarded_ppo_damage_only_objective_smoke_test.py",
    "scripts/guarded_ppo_scratch_control_smoke_test.py",
    "scripts/guarded_ppo_resume_smoke_test.py",
    "scripts/guarded_ppo_cli_execution_gate_smoke_test.py",
    "scripts/guarded_ppo_seed_contract_smoke_test.py",
    "scripts/guarded_ppo_incumbent_best_retention_smoke_test.py",
    "scripts/guarded_ppo_failure_resume_smoke_test.py",
    "scripts/guarded_ppo_orphan_checkpoint_adoption_smoke_test.py",
    "scripts/guarded_ppo_state_integrity_smoke_test.py",
    "scripts/guarded_ppo_route_diagnostics_smoke_test.py",
    "scripts/guarded_ppo_stage_timeout_smoke_test.py",
    "scripts/guarded_ppo_cross_platform_path_canonicalization_smoke_test.py",
    "scripts/guarded_ppo_checkpoint_sidecar_strict_contract_smoke_test.py",
    "scripts/guarded_ppo_completed_experiment_integrity_smoke_test.py",
    "scripts/guarded_ppo_completed_experiment_spot_evaluation_smoke_test.py",
    "scripts/guarded_ppo_route_similarity_diagnostic_only_smoke_test.py",
    "scripts/guarded_ppo_dry_run_step0_alias_smoke_test.py",
    "scripts/ppo_checkpoint_sidecar_smoke_test.py",
    "scripts/guarded_ppo_short_integration_smoke_test.py",
    "scripts/build_candidate_archive_output_guard_smoke_test.py",
    "scripts/beam_search_plan_contract_smoke_test.py",
    "scripts/beam_search_clone_isolation_smoke_test.py",
    "scripts/beam_search_clone_behavioral_parity_smoke_test.py",
    "scripts/beam_search_state_roundtrip_smoke_test.py",
    "scripts/beam_search_state_fingerprint_contract_smoke_test.py",
    "scripts/beam_search_state_payload_size_smoke_test.py",
    "scripts/beam_search_exact_dedup_dominance_smoke_test.py",
    "scripts/beam_search_true_time_bucket_smoke_test.py",
    "scripts/beam_search_legal_action_expansion_smoke_test.py",
    "scripts/beam_search_zero_time_action_smoke_test.py",
    "scripts/beam_search_cutoff_scheduler_smoke_test.py",
    "scripts/beam_search_delayed_payoff_diversity_smoke_test.py",
    "scripts/beam_search_real_diversity_key_contract_smoke_test.py",
    "scripts/beam_search_damage_only_winner_smoke_test.py",
    "scripts/beam_search_manual_route_independence_guard_smoke_test.py",
    "scripts/beam_search_resume_integrity_smoke_test.py",
    "scripts/beam_search_resume_equivalence_smoke_test.py",
    "scripts/beam_search_realistic_2000_resume_equivalence_smoke_test.py",
    "scripts/beam_search_hot_path_scalability_smoke_test.py",
    "scripts/beam_search_checkpoint_interval_smoke_test.py",
    "scripts/beam_search_route_store_compaction_smoke_test.py",
    "scripts/beam_search_diversity_phase_contract_smoke_test.py",
    "scripts/beam_search_future_field_classification_smoke_test.py",
    "scripts/beam_search_short_window_diversity_smoke_test.py",
    "scripts/beam_search_horizon_comparison_guard_smoke_test.py",
    "scripts/beam_search_pending_frontier_bound_smoke_test.py",
    "scripts/beam_search_peak_live_metric_smoke_test.py",
    "scripts/beam_search_intra_bucket_budget_guard_smoke_test.py",
    "scripts/beam_search_partial_node_resume_smoke_test.py",
    "scripts/beam_search_final_replay_reporting_smoke_test.py",
    "scripts/beam_search_terminal_replay_parity_smoke_test.py",
    "scripts/beam_search_completed_route_reporting_contract_smoke_test.py",
    "scripts/beam_search_completion_order_smoke_test.py",
    "scripts/beam_search_memory_bound_contract_smoke_test.py",
    "scripts/beam_search_destination_bucket_test_utils.py",
    "scripts/beam_search_destination_accumulator_hot_path_smoke_test.py",
    "scripts/beam_search_destination_accumulator_spill_smoke_test.py",
    "scripts/beam_search_destination_accumulator_manifest_size_smoke_test.py",
    "scripts/beam_search_compact_cli_output_smoke_test.py",
    "scripts/beam_search_accumulator_metrics_contract_smoke_test.py",
    "scripts/beam_search_duplicate_lineage_tie_smoke_test.py",
    "scripts/beam_search_destination_bucket_order_independence_smoke_test.py",
    "scripts/beam_search_destination_bucket_batch_equivalence_smoke_test.py",
    "scripts/beam_search_destination_bucket_partition_merge_smoke_test.py",
    "scripts/beam_search_destination_bucket_resume_equivalence_smoke_test.py",
    "scripts/beam_search_diversity_quota_fill_smoke_test.py",
    "scripts/beam_search_cli_execution_gate_smoke_test.py",
    "scripts/beam_search_bounded_integration_smoke_test.py",
    "scripts/project_progress_beam_search_alignment_smoke_test.py",
    "scripts/project_progress_beam_search_calibration_alignment_smoke_test.py",
    "scripts/beam_search_calibration_result_integrity_smoke_test.py",
    "scripts/beam_search_calibration_ingestion_idempotence_smoke_test.py",
    "scripts/beam_search_calibration_artifact_path_smoke_test.py",
    "scripts/beam_search_calibration_report_format_smoke_test.py",
    "scripts/progress_dashboard_beam_calibration_alignment_smoke_test.py",
    "scripts/progress_dashboard_beam_calibration_render_smoke_test.py",
    "scripts/final_archive_suite_utils.py",
    "scripts/final_archive_project_progress_suite.py",
    "scripts/final_archive_guarded_ppo_lightweight_suite.py",
    "scripts/final_archive_guarded_ppo_lightweight_contract_smoke_test.py",
    "scripts/final_archive_guarded_ppo_suite_repeatability_smoke_test.py",
    "scripts/final_archive_beam_calibration_suite.py",
    "scripts/final_archive_beam_helper_suite.py",
    "scripts/final_archive_dataset_metadata_suite.py",
    "scripts/final_archive_checker_repeatability_smoke_test.py",
    "scripts/guarded_ppo_state_integrity_repeatability_smoke_test.py",
    "scripts/ingest_beam_search_v111_calibration_results.py",
    "scripts/build_lowmem_beam_workspace.py",
    "scripts/build_lowmem_beam_result_archive.py",
    "scripts/cleanup_unnecessary_runtime_artifacts.py",
    "scripts/beam_search_lowmem_32gb_plan_contract_smoke_test.py",
    "scripts/beam_search_lowmem_workspace_builder_smoke_test.py",
    "scripts/beam_search_lowmem_workspace_manifest_smoke_test.py",
    "scripts/beam_search_lowmem_output_isolation_smoke_test.py",
    "scripts/beam_search_lowmem_memory_guard_smoke_test.py",
    "scripts/beam_search_lowmem_spill_streaming_smoke_test.py",
    "scripts/beam_search_lowmem_spill_finalization_count_smoke_test.py",
    "scripts/beam_search_lowmem_spill_no_repeated_rescan_smoke_test.py",
    "scripts/beam_search_lowmem_probe_phase_timing_smoke_test.py",
    "scripts/beam_search_lowmem_10000_probe_smoke_test.py",
    "scripts/beam_search_lowmem_10000_probe_repeatability_smoke_test.py",
    "scripts/cleanup_unnecessary_runtime_artifacts_smoke_test.py",
    "scripts/project_progress_beam_search_lowmem_alignment_smoke_test.py",
    "data/beam_search_plan_v114_32gb.json",
    "data/beam_search_plan_v115_32gb_resume_v114.json",
    "results/beam_search_v114_3m_checkpoint_review_v115.json",
    "results/beam_search_v114_3m_reviewed_file_inventory_v115.json",
    "results/beam_search_v114_3m_resume_extension_v115_receipt.json",
    "reports/beam_search_v114_3m_checkpoint_review_v115.md",
    "scripts/validate_beam_v114_3m_resume_extension_v115.py",
    "scripts/build_candidate_115_preflight_archive.py",
    "scripts/beam_search_v115_resume_test_utils.py",
    "scripts/beam_search_v115_actual_runner_resume_extension_smoke_test.py",
    "scripts/beam_search_v115_resume_preflight_no_mutation_smoke_test.py",
    "scripts/beam_search_v115_lowmem_execution_gate_smoke_test.py",
    "scripts/beam_search_v115_real_checkpoint_inventory_contract_smoke_test.py",
    "scripts/beam_search_v114_full_stage_scope_smoke_test.py",
    "scripts/beam_search_v114_current_incumbent_selection_smoke_test.py",
    "scripts/beam_search_v115_resume_extension_plan_contract_smoke_test.py",
    "scripts/beam_search_v115_resume_extension_validation_smoke_test.py",
    "scripts/beam_search_v115_resume_extension_mutation_guard_smoke_test.py",
    "scripts/beam_search_v114_3m_checkpoint_review_smoke_test.py",
    "scripts/project_progress_beam_v115_alignment_smoke_test.py",
    "search/beam_performance.py",
    "search/beam_completed_result.py",
    "scripts/ingest_completed_beam_result_v116.py",
    "scripts/cleanup_completed_beam_payload_v116.py",
    "scripts/beam_search_v116_completed_result_integrity_smoke_test.py",
    "scripts/beam_search_v116_winner_replay_parity_smoke_test.py",
    "scripts/beam_search_v116_current_winner_smoke_test.py",
    "scripts/beam_search_resume_performance_accounting_smoke_test.py",
    "scripts/beam_search_v116_route_reference_alignment_smoke_test.py",
    "scripts/beam_search_v116_completed_inventory_smoke_test.py",
    "scripts/beam_search_v116_completed_cleanup_smoke_test.py",
    "scripts/project_progress_beam_completed_v116_alignment_smoke_test.py",
    "scripts/progress_dashboard_beam_completed_v116_smoke_test.py",
    "results/beam_search_v114_completed_v116/result_manifest.json",
    "results/beam_search_v114_completed_v116/final_summary.json",
    "results/beam_search_v114_completed_v116/leaderboard.json",
    "results/beam_search_v114_completed_v116/best_route.json",
    "results/beam_search_v114_completed_v116/winning_route_summary.json",
    "results/beam_search_v114_completed_v116/winning_route_timeline.csv",
    "results/beam_search_v114_completed_v116/corrected_execution_metrics.json",
    "results/beam_search_v114_completed_v116/completed_routes_compact.json",
    "results/beam_search_v114_completed_v116/full_result_inventory.json",
    "results/beam_search_v114_completed_inventory_v116.json",
    "reports/beam_search_v114_completed_v116.md",
    "results/beam_search_v114_lowmem_10000_probe_summary.json",
    "results/manual_120s_baseline_v114_summary.json",
    "results/manual_120s_baseline_v114_timeline.csv",
    "results/manual_model_comparison_v114.json",
    "results/transition_contract_v114_model_reevaluation/leaderboard.json",
    "reports/general_swap_aemeath_outro_v114.md",
    "reports/beam_search_v114_32gb_lowmem.md",
    "reports/manual_120s_baseline_v114.md",
    "reports/transition_contract_v114_model_reevaluation.md",
    "scripts/rebaseline_transition_contract_v114.py",
    "scripts/qte_intro_outro_foundation_smoke_test.py",
    "scripts/generic_swap_no_legacy_placeholder_warning_smoke_test.py",
    "scripts/generic_swap_zero_time_reentry_cooldown_smoke_test.py",
    "scripts/generic_swap_timed_intro_reentry_cooldown_smoke_test.py",
    "scripts/generic_swap_action_mask_observation_smoke_test.py",
    "scripts/generic_swap_zero_time_loop_guard_smoke_test.py",
    "scripts/aemeath_outro_base_buff_smoke_test.py",
    "scripts/aemeath_outro_per_character_upgrade_smoke_test.py",
    "scripts/aemeath_outro_recast_reset_smoke_test.py",
    "scripts/aemeath_outro_timed_intro_order_smoke_test.py",
    "scripts/specific_character_multi_target_buff_smoke_test.py",
    "scripts/swap_outro_clone_restore_resume_smoke_test.py",
    "scripts/v114_excluded_scope_guard_smoke_test.py",
    "scripts/transition_contract_v114_rebaseline_smoke_test.py",
    "scripts/transition_contract_v114_model_reevaluation_smoke_test.py",
    "scripts/beam_search_plan_v114_32gb_contract_smoke_test.py",
    "scripts/beam_search_v114_streaming_spill_contract_smoke_test.py",
    "scripts/aemeath_outro_cast_upgrade_reporting_smoke_test.py",
    "scripts/project_progress_transition_contract_v114_alignment_smoke_test.py",
    "data/mcts_plan_v118_32gb_3x50k.json",
    "reports/mcts_v117_20k_calibration_v118.md",
    "results/mcts_v117_calibration_20k_v118/result_manifest.json",
    "results/mcts_v117_calibration_20k_v118/full_result_inventory.json",
    "scripts/ingest_mcts_v117_20k_calibration_v118.py",
    "scripts/cleanup_mcts_v117_calibration_payload_v118.py",
    "scripts/mcts_v117_20k_calibration_integrity_smoke_test.py",
    "scripts/mcts_v117_20k_winner_replay_parity_smoke_test.py",
    "scripts/mcts_v117_20k_progression_smoke_test.py",
    "scripts/mcts_phase_time_accounting_smoke_test.py",
    "scripts/mcts_phase_time_resume_accounting_smoke_test.py",
    "scripts/mcts_plan_v118_3x50k_contract_smoke_test.py",
    "scripts/mcts_v118_multistage_execution_gate_smoke_test.py",
    "scripts/mcts_v118_seed_output_isolation_smoke_test.py",
    "scripts/mcts_checkpoint_generation_retention_smoke_test.py",
    "scripts/mcts_v117_calibration_cleanup_smoke_test.py",
    "scripts/mcts_v118_compact_inventory_self_contained_smoke_test.py",
    "scripts/project_progress_mcts_v118_alignment_smoke_test.py",
    "scripts/mcts_v118_probe_utils.py",
    "scripts/mcts_v118_3x200_probe_smoke_test.py",
    "scripts/mcts_v118_3x200_probe_repeatability_smoke_test.py",
    "data/mcts_result_role_compatibility_v119.json",
    "search/mcts_result_role.py",
    "search/mcts_production_result.py",
    "reports/mcts_v118_3x50k_production_v119.md",
    "results/mcts_v118_production_3x50k_v119/result_manifest.json",
    "results/mcts_v118_production_3x50k_v119/aggregate_summary.json",
    "results/mcts_v118_production_3x50k_v119/full_result_inventories.json",
    "scripts/ingest_mcts_v118_3x50k_results_v119.py",
    "scripts/cleanup_mcts_v118_production_payloads_v119.py",
    "scripts/mcts_v118_3x50k_integrity_smoke_test.py",
    "scripts/mcts_v118_3x50k_winner_replay_parity_smoke_test.py",
    "scripts/mcts_v118_3x50k_ranking_smoke_test.py",
    "scripts/mcts_v118_3x50k_progression_plateau_smoke_test.py",
    "scripts/mcts_result_role_reporting_smoke_test.py",
    "scripts/mcts_v118_production_metadata_correction_smoke_test.py",
    "scripts/mcts_v119_current_project_comparison_smoke_test.py",
    "scripts/mcts_v118_production_cleanup_smoke_test.py",
    "scripts/project_progress_mcts_v119_alignment_smoke_test.py",
    "scripts/final_archive_fresh_check_coverage_v119_smoke_test.py",
    "scripts/full_real_cycle_integration_smoke_test.py",
    "scripts/rl_observation_shape_guard_smoke_test.py",
    "scripts/rl_party_action_mask_smoke_test.py",
    "scripts/direct_action_manifest_hash_guard_smoke_test.py",
    "scripts/apply_direct_action_data_v61.py",
)
EXPECTED_GUARDED_PLAN_SHA256 = "0306c734347e49460fd7273bce546eed80a2db657e460eb707f5cab961a9e0e6"
TEXT_SUFFIXES = (".py", ".json", ".md", ".txt")
AUTHORITATIVE_SOURCE_FILES = (
    "data/actions.json",
    "direct_action_data_patch_manifest_v61.json",
    "data/source/direct_action_data_patch_manifest_v61.json",
)
CORRECT_SHEET_NAME = "".join(chr(codepoint) for codepoint in (0x58F0, 0x9AB8))
FORBIDDEN_CORRUPTED_SHEET_NAME = "".join(chr(codepoint) for codepoint in (0x9DAF, 0xACC8, 0x3058))
ESTABLISHED_MOJIBAKE_MARKERS = (
    "".join(chr(codepoint) for codepoint in (0x00EF, 0x00BB, 0x00BF)),
    "".join(chr(codepoint) for codepoint in (0x00E9, 0x00B6, 0x00AF, 0x00EA, 0x00B3, 0x02C6, 0x00EC, 0x00A7)),
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument(
        "--orchestration-smoke",
        action="store_true",
        help="Run static archive validation plus aggregate helper suites, without the evaluator lifecycle.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    started = time.perf_counter()
    stats = validate_archive(args.archive, orchestration_smoke=args.orchestration_smoke)
    stats["total_elapsed_seconds"] = round(time.perf_counter() - started, 6)
    stats["orchestration_smoke"] = args.orchestration_smoke
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print("manual_120s_bc_final_archive_integrity_smoke_test ok")


def validate_archive(archive: Path, *, orchestration_smoke: bool = False) -> dict[str, Any]:
    assert archive.exists(), archive
    with zipfile.ZipFile(archive) as zf:
        names = [info.filename for info in zf.infolist()]
        name_set = set(names)
        for required in REQUIRED_FILES:
            assert required in name_set, required
        cache_entries = [name for name in names if _is_cache_entry(name)]
        obsolete_bundle_entries = [
            name for name in names if name.replace("\\", "/") == "bc_eval_bundle/" or name.startswith("bc_eval_bundle/")
        ]
        assert not cache_entries, cache_entries[:20]
        assert not obsolete_bundle_entries, obsolete_bundle_entries
        assert not any(name.startswith("results/beam_search_v114_lowmem_32gb/") for name in names)
        assert not any(name.startswith("results/mcts_v117_32gb/calibration_20k_seed_117001/") for name in names)
        assert not any(name.startswith("results/mcts_v118_32gb/production_50k_seed_") for name in names)
        assert zf.testzip() is None

        route_bytes = zf.read("data/manual_120s_baseline_routes_v104.json")
        assert bytes_sha256(route_bytes) == SOURCE_ROUTE_FILE_SHA256
        _assert_json(zf.read("data/manual_120s_baseline_routes_v104.json"))

        summary = json.loads(zf.read("results/manual_120s_bc_demonstration_v105_summary.json").decode("utf-8"))
        evaluation_summary = json.loads(zf.read("results/ppo_evaluation_summary.json").decode("utf-8"))
        ppo_summary = json.loads(zf.read("results/ppo_100k_evaluation_summary.json").decode("utf-8"))
        comparison = json.loads(zf.read("results/manual_bc_ppo_comparison_v108.json").decode("utf-8"))
        progress = json.loads(zf.read("PROJECT_PROGRESS_STATE.json").decode("utf-8"))
        completed_manifest_path = "results/beam_search_v114_completed_v116/result_manifest.json"
        completed_manifest_bytes = zf.read(completed_manifest_path)
        completed_manifest = json.loads(completed_manifest_bytes.decode("utf-8"))
        completed_progress = progress["current_in_progress_task"]["candidate_116_completed_beam"]
        assert progress["status"]["latest_externally_verified_baseline"] == "118"
        assert progress["status"]["current_candidate"] == "119"
        production_path = "results/mcts_v118_production_3x50k_v119/result_manifest.json"
        production = json.loads(zf.read(production_path).decode("utf-8"))
        production_progress = progress["current_in_progress_task"]["candidate_119_mcts"]
        assert bytes_sha256(zf.read(production_path)) == production_progress["compact_manifest_sha256"]
        assert production["aggregate"]["simulations"] == 150000
        assert production["aggregate"]["winner"]["seed"] == 118003
        assert production["aggregate"]["extension_recommended"] is False
        assert production["external_review_status"] == "pending"
        assert production["global_optimum_proven"] is False
        compact_path = "results/mcts_v117_calibration_20k_v118/result_manifest.json"
        compact = json.loads(zf.read(compact_path).decode("utf-8"))
        compact_progress = progress["current_in_progress_task"]["candidate_117_mcts"]
        assert bytes_sha256(zf.read(compact_path)) == compact_progress["compact_manifest_sha256"]
        assert compact["calibration"]["simulations"] == 20000
        assert compact["calibration"]["winner"]["route_id"] == "5aab329ce5b526a7"
        assert compact["calibration_only"] and not compact["production_mcts_executed"]
        assert bytes_sha256(completed_manifest_bytes) == completed_progress["result_manifest_sha256"]
        assert completed_manifest["termination_status"] == "completed_search"
        assert completed_manifest["completed_search"]["expansions"] == 4908270
        assert completed_manifest["completed_search"]["completed_retained_route_count"] == 128
        assert completed_manifest["completed_search"]["configured_maximum_expansions"] == 6500000
        assert completed_manifest["winning_route"]["route_id"] == "67a4250b3b8d0de9"
        assert completed_manifest["winning_route"]["total_damage"] == 5651892.274552992
        assert completed_manifest["winning_route"]["dps"] == 47099.1022879416
        assert completed_manifest["global_optimum_proven"] is False
        assert completed_manifest["heavy_output_preserved_locally"] is True
        assert completed_manifest["heavy_output_mutated_by_ingestion"] is False
        for artifact, expected_sha256 in completed_manifest["artifact_sha256"].items():
            archive_path = f"results/beam_search_v114_completed_v116/{artifact}"
            assert bytes_sha256(zf.read(archive_path)) == expected_sha256, archive_path
        assert bytes_sha256(zf.read("results/beam_search_v114_completed_inventory_v116.json")) == (
            completed_manifest["external_inventory_artifact_sha256"]
        )
        guarded_plan_bytes = zf.read("data/guarded_ppo_experiment_plan_v109.json")
        assert bytes_sha256(guarded_plan_bytes) == EXPECTED_GUARDED_PLAN_SHA256
        guarded_plan = json.loads(guarded_plan_bytes.decode("utf-8"))
        assert guarded_plan["schema_version"] == "guarded_ppo_experiment_plan_v109"
        assert [branch["branch_id"] for branch in guarded_plan["branches"]] == [
            "bc_conservative_seed_11",
            "bc_exploratory_seed_73",
            "scratch_control_seed_137",
        ]
        beam_plan_bytes = zf.read("data/beam_search_plan_v111.json")
        assert bytes_sha256(beam_plan_bytes) == EXPECTED_BEAM_PLAN_SHA256
        beam_plan = json.loads(beam_plan_bytes.decode("utf-8"))
        assert beam_plan["schema_version"] == "beam_search_plan_v111"
        assert beam_plan["candidate"] == "111"
        assert beam_plan["execution_boundary"]["candidate_111_runs_calibration"] is False
        assert beam_plan["execution_boundary"]["candidate_111_runs_full_search"] is False
        assert beam_plan["execution_boundary"]["candidate_111_runs_mcts"] is False
        assert beam_plan["execution_boundary"]["smoke_max_combat_duration"] == 3.0
        assert beam_plan["execution_boundary"]["smoke_max_expansions"] == 2000
        assert beam_plan["memory_estimate_contract"]["pending_bucket_node_bound"] == "stage.beam_width"
        assert beam_plan["memory_estimate_contract"]["destination_bucket_retention"] == "destination_bucket_accumulator_exact_batch_equivalent"
        assert beam_plan["memory_estimate_contract"]["destination_bucket_accumulator_algorithm"] == "chunked_exact_future_fingerprint_upsert_spill_finalized_by_batch_global_and_diversity_retention"
        assert beam_plan["memory_estimate_contract"]["destination_bucket_no_per_child_full_retained_selection"] is True
        assert beam_plan["memory_estimate_contract"]["destination_bucket_insertion_order_independent"] is True
        assert beam_plan["memory_estimate_contract"]["destination_bucket_partition_merge_independent"] is True
        assert beam_plan["memory_estimate_contract"]["destination_accumulator_unique_fingerprint_bound"] == "stage.destination_accumulator_unique_fingerprint_bound"
        assert beam_plan["memory_estimate_contract"]["destination_accumulator_spill_policy"] == "atomic_compressed_json_gz_chunks_hash_validated_resume_exact"
        assert beam_plan["memory_estimate_contract"]["destination_accumulator_checkpoint_manifest"] == "compact_manifest_with_paths_sha256_counts_and_metrics_no_node_payloads"
        assert beam_plan["memory_estimate_contract"]["compact_cli_output_contract"] == "stdout_summary_only_no_frontier_nodes_route_store_accumulator_payloads_or_timelines"
        assert beam_plan["memory_estimate_contract"]["metric_conservation_contract"] == "candidates_seen_equals_exact_duplicates_plus_unique_fingerprints_and_unique_equals_final_retained_plus_final_rejected"
        assert beam_plan["memory_estimate_contract"]["canonical_route_lineage_tie_contract"] == "lineage_tie_key_before_internal_node_id"
        assert beam_plan["memory_estimate_contract"]["accumulator_index_bytes_per_node"] == 128
        assert beam_plan["memory_estimate_contract"]["limit_check_interval_expansions"] == 64
        assert beam_plan["stages"][0]["destination_accumulator_unique_fingerprint_bound"] == 8192
        assert beam_plan["stages"][1]["destination_accumulator_unique_fingerprint_bound"] == 32768
        assert beam_plan["final_reporting_contract"]["short_horizon_reference_damage_status"] == "horizon_mismatch_not_comparable"
        assert beam_plan["final_reporting_contract"]["short_horizon_numeric_reference_ranking"] is False

        lowmem_plan_bytes = zf.read("data/beam_search_plan_v113_32gb.json")
        assert bytes_sha256(lowmem_plan_bytes) == EXPECTED_LOWMEM_BEAM_PLAN_SHA256
        lowmem_plan = json.loads(lowmem_plan_bytes.decode("utf-8"))
        assert lowmem_plan["schema_version"] == "beam_search_plan_v113_32gb"
        assert lowmem_plan["candidate"] == "113"
        assert lowmem_plan["inherits_contracts_from"] == {
            "path": "data/beam_search_plan_v111.json",
            "sha256": EXPECTED_BEAM_PLAN_SHA256,
        }
        assert lowmem_plan["output_contract"]["canonical_output_root"] == "results/beam_search_v113_lowmem_32gb"
        assert "results/beam_search_v111_full_120s" in lowmem_plan["output_contract"]["forbidden_resume_or_output_roots"]
        assert lowmem_plan["initial_execution_policy"]["first_run_max_expansions"] == 3000000
        assert lowmem_plan["initial_execution_policy"]["plan_maximum_expansions"] == 5000000
        lowmem_stage = lowmem_plan["stages"][0]
        assert len(lowmem_plan["stages"]) == 1
        assert lowmem_stage["stage_id"] == "full_120s_lowmem_32gb"
        assert lowmem_stage["combat_duration"] == 120.0
        assert lowmem_stage["beam_width"] == 1792
        assert lowmem_stage["global_damage_quota"] == 896
        assert lowmem_stage["diversity_retention_quota"] == 896
        assert lowmem_stage["maximum_expansions"] == 5000000
        assert lowmem_stage["memory_budget_bytes"] == 23622320128
        assert lowmem_stage["wall_clock_budget_seconds"] == 36000
        assert lowmem_stage["destination_accumulator_unique_fingerprint_bound"] == 16384
        assert lowmem_stage["in_memory_accumulator_candidate_limit"] == 4096
        assert lowmem_stage["disk_spill_enabled"] is True

        v114_plan_bytes = zf.read("data/beam_search_plan_v114_32gb.json")
        assert bytes_sha256(v114_plan_bytes) == EXPECTED_V114_BEAM_PLAN_SHA256
        v114_plan = json.loads(v114_plan_bytes.decode("utf-8"))
        assert v114_plan["schema_version"] == "beam_search_plan_v114_32gb"
        assert v114_plan["candidate"] == 114
        assert v114_plan["transition_contract"] == {
            "version": "v114",
            "generic_swap_action_time": 0.0,
            "generic_swap_combat_time_cost": 0.0,
            "generic_swap_source_status": "user_approved_benchmark_assumption_after_workbook_and_web_review",
            "swap_reentry_cooldown_seconds": 1.0,
            "swap_reentry_cooldown_clock": "combat_time",
            "aemeath_outro_implementation_version": "implemented_v114",
        }
        assert v114_plan["output_contract"]["canonical_output_root"] == "results/beam_search_v114_lowmem_32gb"
        assert set(v114_plan["output_contract"]["forbidden_resume_or_output_roots"]) == {
            "results/beam_search_v111_full_120s",
            "results/beam_search_v113_lowmem_32gb",
        }
        assert v114_plan["execution_boundary"] == {
            "candidate_114_runs_3m_search": False,
            "candidate_114_runs_5m_search": False,
            "candidate_114_runs_mcts": False,
            "candidate_114_runs_training": False,
            "bounded_probe_max_expansions": 10000,
        }
        assert v114_plan["stages"][0]["stage_id"] == "full_120s_lowmem_32gb_v114"
        assert v114_plan["stages"][0]["accumulator_spill_format"] == "streaming_jsonl_gzip_v113"
        v115_plan_bytes = zf.read("data/beam_search_plan_v115_32gb_resume_v114.json")
        v115_plan = json.loads(v115_plan_bytes.decode("utf-8"))
        assert bytes_sha256(v115_plan_bytes) == progress["current_in_progress_task"]["candidate_115_beam_correction"]["plan_sha256"]
        assert v115_plan["execution_contract"]["low_memory_32gb"] is True
        assert v115_plan["execution_contract"]["hard_memory_budget_required"] is True
        assert v115_plan["execution_contract"]["canonical_output_root_required_for_resume"] is True
        assert v115_plan["stages"][0]["maximum_expansions"] == 6500000
        reviewed_inventory_bytes = zf.read("results/beam_search_v114_3m_reviewed_file_inventory_v115.json")
        assert bytes_sha256(reviewed_inventory_bytes) == v115_plan["source_checkpoint_contract"]["reviewed_inventory_file_sha256"]
        reviewed_inventory = json.loads(reviewed_inventory_bytes.decode("utf-8"))
        assert reviewed_inventory["file_count"] == 649
        assert reviewed_inventory["total_bytes"] == 1752618157
        assert reviewed_inventory["inventory_sha256"] == "0bb00535354717d05ae1761fe6522bcc5129cc598cc8aaf072843626a7d43f15"
        receipt_bytes = zf.read("results/beam_search_v114_3m_resume_extension_v115_receipt.json")
        assert bytes_sha256(receipt_bytes) == progress["current_in_progress_task"]["candidate_115_beam_correction"]["resume_receipt_sha256"]
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt["source_best_partial_combat_time"] == 67.48333333333329
        assert receipt["source_best_partial_current_time"] == 107.75000000000001
        assert receipt["source_best_partial_total_damage"] == 2850679.8061139295
        assert receipt["source_best_partial_action_count"] == 92
        assert bytes_sha256(zf.read("data/transition_config.json")) == EXPECTED_V114_TRANSITION_CONFIG_SHA256
        assert bytes_sha256(zf.read("data/buffs.json")) == EXPECTED_V114_BUFFS_SHA256
        v114_manual = json.loads(zf.read("results/manual_120s_baseline_v114_summary.json").decode("utf-8"))
        assert v114_manual["candidate"] == 114
        assert v114_manual["external_review_status"] == "pending"
        assert v114_manual["route_valid"] is True
        assert v114_manual["invalid_action_count"] == 0
        _assert_close(v114_manual["total_damage"], 5268418.084869607)
        _assert_close(v114_manual["dps"], 43903.484040580064)
        assert v114_manual["aemeath_outro_cast_count"] == 3
        assert v114_manual["aemeath_outro_upgrade_count"] == 3
        v114_leaderboard = json.loads(
            zf.read("results/transition_contract_v114_model_reevaluation/leaderboard.json").decode("utf-8")
        )
        v114_evaluation_entries = sorted(
            name
            for name in name_set
            if name.startswith("results/transition_contract_v114_model_reevaluation/evaluations/")
            and name.endswith(".json")
        )
        assert len(v114_evaluation_entries) == 32
        for evaluation_entry in v114_evaluation_entries:
            evaluation = json.loads(zf.read(evaluation_entry).decode("utf-8"))
            assert evaluation["candidate"] == 114
            assert evaluation["completed_120s"] is True
            assert evaluation["invalid_action_count"] == 0
        assert v114_leaderboard["candidate"] == 114
        assert v114_leaderboard["evaluation_count"] == 32
        assert v114_leaderboard["winner"]["model_path"] == (
            "models/guarded_ppo_v109/bc_conservative_seed_11/step_000090000.zip"
        )
        _assert_close(v114_leaderboard["winner"]["total_damage"], 5276844.358692044)
        assert v114_leaderboard["winner"]["invalid_action_count"] == 0
        winner_result = json.loads(
            zf.read(
                "results/transition_contract_v114_model_reevaluation/evaluations/"
                "guarded_ppo_v109__bc_conservative_seed_11__step_000090000.zip.json"
            ).decode("utf-8")
        )
        assert winner_result["aemeath_outro_cast_count"] == 3
        assert winner_result["aemeath_outro_upgrade_count"] == 3
        model_bytes = zf.read("models/maskable_ppo_bc_v105.zip")
        assert bytes_sha256(model_bytes) == EXPECTED_BC_MODEL_SHA256
        ppo_model_bytes = zf.read("models/maskable_ppo_candidate_after_bc_v105.zip")
        assert bytes_sha256(ppo_model_bytes) == EXPECTED_PPO_MODEL_SHA256
        guarded_stats = _assert_guarded_completed_archive(zf, name_set)
        _assert_evaluation_summary(evaluation_summary)
        _assert_ppo_evaluation_summary(ppo_summary)
        _assert_comparison(comparison)
        npz_bytes = zf.read("data/generated/manual_120s_bc_demonstration_v105.npz")
        npz_sha = bytes_sha256(npz_bytes)
        assert summary["dataset_sha256"] == npz_sha
        assert _progress_contains(progress, npz_sha)
        assert summary["metadata"]["source_route_file_sha256"] == SOURCE_ROUTE_FILE_SHA256

        manifest_a = zf.read("direct_action_data_patch_manifest_v61.json")
        manifest_b = zf.read("data/source/direct_action_data_patch_manifest_v61.json")
        assert manifest_a == manifest_b
        assert bytes_sha256(manifest_a) == DIRECT_ACTION_MANIFEST_SHA256

        text_stats = scan_archive_text(zf, names)
        assert text_stats["utf8_bom_count"] == 0
        assert text_stats["replacement_character_count"] == 0
        assert text_stats["forbidden_corrupted_sheet_occurrence_count"] == 0
        assert text_stats["established_mojibake_occurrence_count"] == 0
        assert text_stats["correct_sheet_occurrence_count"] > 0
        assert text_stats["authoritative_correct_sheet_occurrence_count"] > 0

    fresh_extraction_results = run_fresh_extraction_checks(archive, orchestration_smoke=orchestration_smoke)
    if DEFAULT_DEMO_PATH.exists():
        assert _sha256_file(DEFAULT_DEMO_PATH) == npz_sha
    return {
        "archive": archive.as_posix(),
        "archive_sha256": _sha256_file(archive),
        "zip_entry_count": len(names),
        "cache_entry_count": len(cache_entries),
        "crc_error_entry": None,
        "obsolete_bc_eval_bundle_entry_count": len(obsolete_bundle_entries),
        "route_sha256": SOURCE_ROUTE_FILE_SHA256,
        "npz_sha256": npz_sha,
        "bc_model_sha256": EXPECTED_BC_MODEL_SHA256,
        "ppo_model_sha256": EXPECTED_PPO_MODEL_SHA256,
        **guarded_stats,
        "direct_action_manifest_sha256": DIRECT_ACTION_MANIFEST_SHA256,
        "v114_beam_plan_sha256": EXPECTED_V114_BEAM_PLAN_SHA256,
        "v114_transition_config_sha256": EXPECTED_V114_TRANSITION_CONFIG_SHA256,
        "v114_buffs_sha256": EXPECTED_V114_BUFFS_SHA256,
        **text_stats,
        "fresh_extraction_checks": fresh_extraction_results,
    }


def _assert_guarded_completed_archive(zf: zipfile.ZipFile, name_set: set[str]) -> dict[str, Any]:
    state = json.loads(zf.read("results/guarded_ppo_v109/experiment_state.json").decode("utf-8"))
    final_summary = json.loads(zf.read("results/guarded_ppo_v109/final_experiment_summary.json").decode("utf-8"))
    best = json.loads(zf.read("results/guarded_ppo_v109/best_checkpoint.json").decode("utf-8"))
    leaderboard = json.loads(zf.read("results/guarded_ppo_v109/leaderboard.json").decode("utf-8"))
    assert state["plan_sha256"] == EXPECTED_GUARDED_PLAN_SHA256
    assert final_summary["plan_sha256"] == EXPECTED_GUARDED_PLAN_SHA256
    assert final_summary["candidate"] == "110"
    assert final_summary["latest_verified_baseline"] == "109"
    assert final_summary["no_guarded_checkpoint_exceeded_bc"] is True
    assert final_summary["global_optimum_proven"] is False
    assert final_summary["route_similarity_usage"] == "diagnostic_only_not_used_for_winner_selection"
    provenance = state["completed_experiment_provenance"]
    assert provenance["trained_branch_count"] == 3
    assert provenance["trained_checkpoint_count"] == 30
    assert provenance["failed_chunk_count"] == 0
    assert provenance["requested_aggregate_timesteps"] == 300000
    assert provenance["actual_aggregate_model_timesteps"] == 307200
    assert best["winner_kind"] == "verified_bc_model"
    assert best["model_path"] == "models/maskable_ppo_bc_v105.zip"
    _assert_close(best["total_damage"], EXPECTED_EVAL_TOTAL_DAMAGE)
    assert leaderboard["global_best"]["winner_kind"] == "verified_bc_model"

    guarded_models: list[str] = []
    guarded_sidecars: list[str] = []
    guarded_summaries: list[str] = []
    guarded_timelines: list[str] = []
    for branch_id, branch_state in state["branches"].items():
        records = [item for item in branch_state["chunks"] if item.get("kind") == "guarded_ppo_checkpoint"]
        assert len(records) == 10
        assert [item["chunk_index"] for item in records] == list(range(1, 11))
        expected_seed = 11 if branch_id == "bc_conservative_seed_11" else 73 if branch_id == "bc_exploratory_seed_73" else 137
        assert [item["actual_model_seed"] for item in records] == list(range(expected_seed, expected_seed + 10))
        for record in records:
            model_path = record["checkpoint_path"]
            sidecar_path = record["metadata_path"]
            summary_path = record["summary_path"]
            timeline_path = record["timeline_path"]
            for required in (model_path, sidecar_path, summary_path, timeline_path):
                assert required in name_set, required
            assert bytes_sha256(zf.read(model_path)) == record["checkpoint_sha256"]
            assert bytes_sha256(zf.read(sidecar_path)) == record["metadata_sha256"]
            assert bytes_sha256(zf.read(summary_path)) == record["summary_sha256"]
            assert bytes_sha256(zf.read(timeline_path)) == record["timeline_sha256"]
            with zipfile.ZipFile(io.BytesIO(zf.read(model_path))) as model_zip:
                model_data = json.loads(model_zip.read("data").decode("utf-8"))
            assert int(model_data["seed"]) == int(record["actual_model_seed"])
            assert int(model_data["num_timesteps"]) == int(record["actual_model_num_timesteps"])
            assert int(model_data["n_steps"]) == 512
            sidecar = json.loads(zf.read(sidecar_path).decode("utf-8"))
            assert sidecar["model_path"] == model_path
            assert sidecar["model_sha256"] == record["checkpoint_sha256"]
            assert sidecar["actual_model_seed"] == record["actual_model_seed"]
            assert sidecar["actual_model_num_timesteps"] == record["actual_model_num_timesteps"]
            guarded_models.append(model_path)
            guarded_sidecars.append(sidecar_path)
            guarded_summaries.append(summary_path)
            guarded_timelines.append(timeline_path)

    zip_entries = {name for name in name_set if name.endswith(".zip")}
    expected_zip_entries = {
        "models/maskable_ppo_bc_v105.zip",
        "models/maskable_ppo_candidate_after_bc_v105.zip",
        *guarded_models,
    }
    assert zip_entries == expected_zip_entries
    assert len(guarded_models) == 30
    assert len(guarded_sidecars) == 30
    assert len(guarded_summaries) == 30
    assert len(guarded_timelines) == 30
    return {
        "guarded_model_zip_count": len(guarded_models),
        "guarded_sidecar_count": len(guarded_sidecars),
        "guarded_summary_count": len(guarded_summaries),
        "guarded_timeline_count": len(guarded_timelines),
        "guarded_requested_aggregate_timesteps": provenance["requested_aggregate_timesteps"],
        "guarded_actual_aggregate_model_timesteps": provenance["actual_aggregate_model_timesteps"],
    }


def scan_archive_text(zf: zipfile.ZipFile, names: list[str]) -> dict[str, int]:
    stats = {
        "text_entry_count": 0,
        "utf8_bom_count": 0,
        "replacement_character_count": 0,
        "forbidden_corrupted_sheet_occurrence_count": 0,
        "established_mojibake_occurrence_count": 0,
        "correct_sheet_occurrence_count": 0,
        "authoritative_correct_sheet_occurrence_count": 0,
    }
    for name in names:
        if not name.endswith(TEXT_SUFFIXES):
            continue
        data = zf.read(name)
        stats["text_entry_count"] += 1
        if data.startswith(b"\xef\xbb\xbf"):
            stats["utf8_bom_count"] += 1
        text = data.decode("utf-8")
        stats["replacement_character_count"] += text.count("\uFFFD")
        stats["forbidden_corrupted_sheet_occurrence_count"] += text.count(FORBIDDEN_CORRUPTED_SHEET_NAME)
        stats["correct_sheet_occurrence_count"] += text.count(CORRECT_SHEET_NAME)
        if name in AUTHORITATIVE_SOURCE_FILES:
            stats["authoritative_correct_sheet_occurrence_count"] += text.count(CORRECT_SHEET_NAME)
        for marker in ESTABLISHED_MOJIBAKE_MARKERS:
            stats["established_mojibake_occurrence_count"] += text.count(marker)
        if name.endswith(".json"):
            _assert_json(data)
    return stats


def candidate_119_fresh_extraction_check_commands() -> list[list[str]]:
    candidate_119_checks = [
        [sys.executable, "scripts/mcts_v118_3x50k_integrity_smoke_test.py"],
        [sys.executable, "scripts/mcts_v118_3x50k_winner_replay_parity_smoke_test.py"],
        [sys.executable, "scripts/mcts_v118_3x50k_ranking_smoke_test.py"],
        [sys.executable, "scripts/mcts_v118_3x50k_progression_plateau_smoke_test.py"],
        [sys.executable, "scripts/mcts_result_role_reporting_smoke_test.py"],
        [sys.executable, "scripts/mcts_v118_production_metadata_correction_smoke_test.py"],
        [sys.executable, "scripts/mcts_v119_current_project_comparison_smoke_test.py"],
        [sys.executable, "scripts/mcts_v118_production_cleanup_smoke_test.py"],
        [sys.executable, "scripts/project_progress_mcts_v119_alignment_smoke_test.py"],
        [sys.executable, "scripts/final_archive_fresh_check_coverage_v119_smoke_test.py"],
    ]
    return candidate_119_checks


def legacy_fresh_extraction_check_commands() -> list[list[str]]:
    legacy_checks = [
        [sys.executable, "scripts/qte_intro_outro_foundation_smoke_test.py"],
        [sys.executable, "scripts/generic_swap_no_legacy_placeholder_warning_smoke_test.py"],
        [sys.executable, "scripts/generic_swap_zero_time_reentry_cooldown_smoke_test.py"],
        [sys.executable, "scripts/generic_swap_timed_intro_reentry_cooldown_smoke_test.py"],
        [sys.executable, "scripts/generic_swap_action_mask_observation_smoke_test.py"],
        [sys.executable, "scripts/generic_swap_zero_time_loop_guard_smoke_test.py"],
        [sys.executable, "scripts/aemeath_outro_base_buff_smoke_test.py"],
        [sys.executable, "scripts/aemeath_outro_per_character_upgrade_smoke_test.py"],
        [sys.executable, "scripts/aemeath_outro_recast_reset_smoke_test.py"],
        [sys.executable, "scripts/aemeath_outro_timed_intro_order_smoke_test.py"],
        [sys.executable, "scripts/aemeath_outro_cast_upgrade_reporting_smoke_test.py"],
        [sys.executable, "scripts/specific_character_multi_target_buff_smoke_test.py"],
        [sys.executable, "scripts/swap_outro_clone_restore_resume_smoke_test.py"],
        [sys.executable, "scripts/v114_excluded_scope_guard_smoke_test.py"],
        [sys.executable, "scripts/transition_contract_v114_rebaseline_smoke_test.py"],
        [sys.executable, "scripts/transition_contract_v114_model_reevaluation_smoke_test.py"],
        [sys.executable, "scripts/beam_search_plan_v114_32gb_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v114_streaming_spill_contract_smoke_test.py"],
        [sys.executable, "scripts/project_progress_transition_contract_v114_alignment_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v116_completed_result_integrity_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v116_winner_replay_parity_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v116_current_winner_smoke_test.py"],
        [sys.executable, "scripts/beam_search_resume_performance_accounting_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v116_route_reference_alignment_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v116_completed_inventory_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v116_completed_cleanup_smoke_test.py"],
        [sys.executable, "scripts/project_progress_beam_completed_v116_alignment_smoke_test.py"],
        [sys.executable, "scripts/progress_dashboard_beam_completed_v116_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v115_actual_runner_resume_extension_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v115_resume_preflight_no_mutation_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v115_lowmem_execution_gate_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v115_real_checkpoint_inventory_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v115_resume_extension_plan_contract_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v115_resume_extension_validation_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v115_resume_extension_mutation_guard_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v114_full_stage_scope_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v114_current_incumbent_selection_smoke_test.py"],
        [sys.executable, "scripts/beam_search_v114_3m_checkpoint_review_smoke_test.py"],
        [sys.executable, "scripts/project_progress_beam_v115_alignment_smoke_test.py"],
        [sys.executable, "scripts/mcts_plan_v117_32gb_contract_smoke_test.py"],
        [sys.executable, "scripts/mcts_search_independence_smoke_test.py"],
        [sys.executable, "scripts/mcts_state_clone_behavioral_parity_smoke_test.py"],
        [sys.executable, "scripts/mcts_lightweight_action_execution_parity_smoke_test.py"],
        [sys.executable, "scripts/mcts_lightweight_rollout_state_parity_smoke_test.py"],
        [sys.executable, "scripts/mcts_snapshot_reconstruction_smoke_test.py"],
        [sys.executable, "scripts/mcts_uct_progressive_widening_smoke_test.py"],
        [sys.executable, "scripts/mcts_mast_rollout_determinism_smoke_test.py"],
        [sys.executable, "scripts/mcts_action_mask_zero_time_loop_guard_smoke_test.py"],
        [sys.executable, "scripts/mcts_selection_action_limit_smoke_test.py"],
        [sys.executable, "scripts/mcts_selection_zero_time_limit_smoke_test.py"],
        [sys.executable, "scripts/mcts_no_legal_tree_node_smoke_test.py"],
        [sys.executable, "scripts/mcts_checkpoint_resume_equivalence_smoke_test.py"],
        [sys.executable, "scripts/mcts_checkpoint_corruption_no_mutation_smoke_test.py"],
        [sys.executable, "scripts/mcts_previous_checkpoint_fallback_smoke_test.py"],
        [sys.executable, "scripts/mcts_memory_budget_guard_smoke_test.py"],
        [sys.executable, "scripts/mcts_output_root_isolation_smoke_test.py"],
        [sys.executable, "scripts/mcts_completed_route_replay_parity_smoke_test.py"],
        [sys.executable, "scripts/mcts_reporting_current_winner_smoke_test.py"],
        [sys.executable, "search/run_mcts.py", "--plan", "data/mcts_plan_v117_32gb.json", "--dry-run-plan"],
        [sys.executable, "scripts/mcts_200_probe_smoke_test.py"],
        [sys.executable, "scripts/mcts_200_probe_repeatability_smoke_test.py"],
        [sys.executable, "scripts/project_progress_mcts_v117_alignment_smoke_test.py"],
        [sys.executable, "scripts/mcts_v117_20k_calibration_integrity_smoke_test.py"],
        [sys.executable, "scripts/mcts_v117_20k_winner_replay_parity_smoke_test.py"],
        [sys.executable, "scripts/mcts_v117_20k_progression_smoke_test.py"],
        [sys.executable, "scripts/mcts_phase_time_accounting_smoke_test.py"],
        [sys.executable, "scripts/mcts_phase_time_resume_accounting_smoke_test.py"],
        [sys.executable, "scripts/mcts_plan_v118_3x50k_contract_smoke_test.py"],
        [sys.executable, "scripts/mcts_v118_multistage_execution_gate_smoke_test.py"],
        [sys.executable, "scripts/mcts_v118_seed_output_isolation_smoke_test.py"],
        [sys.executable, "scripts/mcts_checkpoint_generation_retention_smoke_test.py"],
        [sys.executable, "scripts/project_progress_mcts_v118_alignment_smoke_test.py"],
        [sys.executable, "scripts/mcts_v118_compact_inventory_self_contained_smoke_test.py"],
        [sys.executable, "scripts/mcts_v117_calibration_cleanup_smoke_test.py"],
        [sys.executable, "search/run_mcts.py", "--plan", "data/mcts_plan_v118_32gb_3x50k.json", "--dry-run-plan"],
        [sys.executable, "scripts/mcts_v118_3x200_probe_smoke_test.py"],
        [sys.executable, "scripts/mcts_v118_3x200_probe_repeatability_smoke_test.py"],
        [sys.executable, "scripts/final_archive_guarded_ppo_lightweight_suite.py"],
        [sys.executable, "scripts/guarded_ppo_stage_timeout_smoke_test.py"],
        [sys.executable, "scripts/beam_search_calibration_result_integrity_smoke_test.py"],
        [sys.executable, "scripts/final_archive_dataset_metadata_suite.py"],
        [sys.executable, "scripts/beam_search_lowmem_workspace_builder_smoke_test.py"],
        [sys.executable, "scripts/beam_search_lowmem_workspace_manifest_smoke_test.py"],
        [sys.executable, "scripts/beam_search_lowmem_memory_guard_smoke_test.py"],
        [sys.executable, "scripts/beam_search_lowmem_spill_streaming_smoke_test.py"],
        [sys.executable, "scripts/beam_search_lowmem_spill_finalization_count_smoke_test.py"],
        [sys.executable, "scripts/beam_search_lowmem_spill_no_repeated_rescan_smoke_test.py"],
        [sys.executable, "scripts/beam_search_destination_bucket_order_independence_smoke_test.py"],
        [sys.executable, "scripts/beam_search_destination_bucket_partition_merge_smoke_test.py"],
        [sys.executable, "scripts/beam_search_realistic_2000_resume_equivalence_smoke_test.py"],
        [sys.executable, "scripts/beam_search_terminal_replay_parity_smoke_test.py"],
        [sys.executable, "scripts/full_real_cycle_integration_smoke_test.py"],
        [sys.executable, "scripts/rl_observation_shape_guard_smoke_test.py"],
        [sys.executable, "scripts/rl_party_action_mask_smoke_test.py"],
        [sys.executable, "scripts/direct_action_manifest_hash_guard_smoke_test.py"],
        [sys.executable, "scripts/apply_direct_action_data_v61.py", "--check", "--fail-on-diff"],
        [
            sys.executable,
            "search/run_beam_search.py",
            "--plan",
            "data/beam_search_plan_v114_32gb.json",
            "--dry-run-plan",
        ],
        [
            sys.executable,
            "scripts/beam_search_lowmem_10000_probe_smoke_test.py",
            "--plan",
            "data/beam_search_plan_v114_32gb.json",
        ],
        [
            sys.executable,
            "scripts/beam_search_lowmem_10000_probe_repeatability_smoke_test.py",
            "--plan",
            "data/beam_search_plan_v114_32gb.json",
        ],
        [sys.executable, "scripts/cleanup_unnecessary_runtime_artifacts_smoke_test.py"],
    ]
    return legacy_checks


def fresh_extraction_check_commands() -> list[list[str]]:
    checks = candidate_119_fresh_extraction_check_commands() + legacy_fresh_extraction_check_commands()
    normalized = [tuple(command[1:]) for command in checks]
    if len(normalized) != len(set(normalized)):
        raise AssertionError("fresh-extraction command provider contains duplicate commands")
    return checks


def run_fresh_extraction_checks(archive: Path, *, orchestration_smoke: bool) -> list[dict[str, Any]]:
    checks = fresh_extraction_check_commands()
    passed: list[dict[str, Any]] = []
    temp_dir = Path(tempfile.mkdtemp(prefix="archive-integrity-"))
    try:
        extract_root = temp_dir / "project"
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract_root)
        for command in checks:
            result = _run(command, cwd=extract_root, timeout=240)
            passed.append(
                {
                    "command": " ".join(command[1:]),
                    "elapsed_seconds": round(result["elapsed_seconds"], 6),
                }
            )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=False)
    return passed


def _assert_json(data: bytes) -> None:
    json.loads(data.decode("utf-8"))


def _assert_evaluation_summary(summary: dict[str, Any]) -> None:
    assert summary["selected_action_count"] == 148
    assert summary["resolved_action_count"] == 148
    assert summary["selected_sequence_sha256"] == EXPECTED_EVAL_SELECTED_SEQUENCE_SHA256
    assert summary["resolved_sequence_sha256"] == EXPECTED_EVAL_RESOLVED_SEQUENCE_SHA256
    assert summary["manual_baseline_selected_sequence_match"] is True
    assert summary["manual_baseline_resolved_sequence_match"] is True
    assert summary["manual_baseline_character_damage_match"] is True
    assert summary["model_metadata_mismatches"] == {}
    assert summary["model_space_mismatches"] == {}
    _assert_close(summary["total_damage"], EXPECTED_EVAL_TOTAL_DAMAGE)
    _assert_close(summary["dps"], EXPECTED_EVAL_DPS)
    for character_id, expected_damage in EXPECTED_DAMAGE_BY_CHARACTER.items():
        _assert_close(summary["damage_by_character"][character_id], expected_damage)
    role_breakdown = summary["effective_damage_role_breakdown"]
    _assert_close(role_breakdown["scheduled_damage"], EXPECTED_SCHEDULED_DAMAGE)
    _assert_close(role_breakdown["total_damage_delta"], 0.0)


def _assert_ppo_evaluation_summary(summary: dict[str, Any]) -> None:
    assert summary["selected_action_count"] == 152
    assert summary["resolved_action_count"] == 152
    assert summary["selected_sequence_sha256"] == EXPECTED_PPO_SELECTED_SEQUENCE_SHA256
    assert summary["resolved_sequence_sha256"] == EXPECTED_PPO_RESOLVED_SEQUENCE_SHA256
    assert summary["manual_baseline_selected_sequence_match"] is False
    assert summary["manual_baseline_resolved_sequence_match"] is False
    assert summary["manual_baseline_character_damage_match"] is False
    assert summary["model_metadata_mismatches"] == {}
    assert summary["model_space_mismatches"] == {}
    assert summary["model_training_metadata_source"] == "ppo_model_sidecar"
    assert summary["model_training_metadata_path"] == "models/maskable_ppo_candidate_after_bc_v105.zip.ppo_metadata.json"
    _assert_close(summary["total_damage"], EXPECTED_PPO_TOTAL_DAMAGE)
    _assert_close(summary["dps"], EXPECTED_PPO_DPS)
    _assert_close(summary["final_time"], 120.0)
    _assert_close(summary["manual_baseline_total_damage"], 5165134.682363359)
    _assert_close(summary["manual_baseline_damage_ratio"], 0.6971042094839032)
    _assert_close(summary["manual_baseline_damage_delta"], -1564497.5527365585)
    for character_id, expected_damage in EXPECTED_PPO_DAMAGE_BY_CHARACTER.items():
        _assert_close(summary["damage_by_character"][character_id], expected_damage)
    role_breakdown = summary["effective_damage_role_breakdown"]
    _assert_close(role_breakdown["scheduled_damage"], EXPECTED_PPO_SCHEDULED_DAMAGE)
    _assert_close(role_breakdown["total_damage_delta"], 0.0)


def _assert_comparison(comparison: dict[str, Any]) -> None:
    assert comparison["schema_version"] == "manual_bc_ppo_comparison_v108"
    assert comparison["objective"] == "final_120_second_total_damage_only"
    assert comparison["winner"] == "bc_model"
    assert comparison["winner_model"] == "models/maskable_ppo_bc_v105.zip"
    assert comparison["ppo_candidate_classification"] == "valid_but_regressed"
    assert comparison["models"]["bc_model"]["sha256"] == EXPECTED_BC_MODEL_SHA256
    assert comparison["models"]["ppo_100k_candidate"]["sha256"] == EXPECTED_PPO_MODEL_SHA256
    results = comparison["results"]
    _assert_close(results["bc_model"]["total_damage"], EXPECTED_EVAL_TOTAL_DAMAGE)
    _assert_close(results["ppo_100k"]["total_damage"], EXPECTED_PPO_TOTAL_DAMAGE)
    assert results["ppo_100k"]["first_selected_action_divergence"] == {
        "zero_based_step": 4,
        "baseline": "aemeath_resonance_skill",
        "ppo": "swap_to_mornye",
    }


def _assert_close(actual: float, expected: float, *, tolerance: float = 1e-6) -> None:
    assert abs(float(actual) - expected) <= tolerance, (actual, expected)


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_cache_entry(name: str) -> bool:
    normalized = name.replace("\\", "/")
    parts = normalized.split("/")
    return (
        "__pycache__" in parts
        or ".pytest_cache" in parts
        or normalized.endswith((".pyc", ".pyo"))
    )


def _progress_contains(progress: object, value: str) -> bool:
    if isinstance(progress, dict):
        return any(_progress_contains(item, value) for item in progress.values())
    if isinstance(progress, list):
        return any(_progress_contains(item, value) for item in progress)
    return progress == value


def _run(command: list[str], *, cwd: Path, timeout: float) -> dict[str, Any]:
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    label = " ".join(command[1:])
    print(f"fresh-extraction check start: {label}", flush=True)
    started = time.perf_counter()
    stdout_fd, stdout_name = tempfile.mkstemp(prefix="archive-check-stdout-", suffix=".txt")
    stderr_fd, stderr_name = tempfile.mkstemp(prefix="archive-check-stderr-", suffix=".txt")
    os.close(stdout_fd)
    os.close(stderr_fd)
    stdout_path = Path(stdout_name)
    stderr_path = Path(stderr_name)
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process_kwargs: dict[str, Any] = {
        "cwd": cwd,
        "env": env,
        "stdout": None,
        "stderr": None,
        "creationflags": creationflags,
        "text": False,
    }
    if os.name != "nt":
        process_kwargs["start_new_session"] = True
    try:
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process_kwargs["stdout"] = stdout_file
            process_kwargs["stderr"] = stderr_file
            process = subprocess.Popen(command, **process_kwargs)
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                _terminate_process_tree(process)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    _kill_process_tree(process)
                    process.wait(timeout=10)
                elapsed = time.perf_counter() - started
                stdout_file.flush()
                stderr_file.flush()
                raise AssertionError(
                    _format_process_failure(
                        command=command,
                        timeout=timeout,
                        elapsed=elapsed,
                        stdout=_read_text(stdout_path),
                        stderr=_read_text(stderr_path),
                    )
                ) from exc
            elapsed = time.perf_counter() - started
            stdout_file.flush()
            stderr_file.flush()
        stdout = _read_text(stdout_path)
        stderr = _read_text(stderr_path)
        if returncode != 0:
            raise AssertionError(
                _format_process_failure(
                    command=command,
                    timeout=timeout,
                    elapsed=elapsed,
                    stdout=stdout,
                    stderr=stderr,
                    returncode=returncode,
                )
            )
        print(f"fresh-extraction check ok: {label} ({elapsed:.3f}s)", flush=True)
        return {"elapsed_seconds": elapsed, "stdout": stdout, "stderr": stderr}
    finally:
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def _kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def _format_process_failure(
    *,
    command: list[str],
    timeout: float,
    elapsed: float,
    stdout: str,
    stderr: str,
    returncode: int | None = None,
) -> str:
    status = f"returncode={returncode}" if returncode is not None else "timeout"
    return (
        f"Fresh extraction check failed ({status})\n"
        f"command: {' '.join(command)}\n"
        f"timeout_seconds: {timeout}\n"
        f"elapsed_seconds: {elapsed:.6f}\n"
        f"stdout:\n{stdout}\n"
        f"stderr:\n{stderr}"
    )


if __name__ == "__main__":
    main()
