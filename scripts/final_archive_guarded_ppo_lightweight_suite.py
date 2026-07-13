from __future__ import annotations

from final_archive_suite_utils import assert_helper_level_scripts, run_script_mains


PURE_CHECKS = (
    "guarded_ppo_completed_experiment_integrity_smoke_test.py",
    "guarded_ppo_route_similarity_diagnostic_only_smoke_test.py",
    "guarded_ppo_plan_contract_smoke_test.py",
    "guarded_ppo_branch_continuation_smoke_test.py",
    "guarded_ppo_damage_only_objective_smoke_test.py",
    "guarded_ppo_scratch_control_smoke_test.py",
    "guarded_ppo_cli_execution_gate_smoke_test.py",
    "guarded_ppo_seed_contract_smoke_test.py",
    "guarded_ppo_incumbent_best_retention_smoke_test.py",
    "guarded_ppo_state_integrity_smoke_test.py",
    "guarded_ppo_state_integrity_repeatability_smoke_test.py",
    "guarded_ppo_route_diagnostics_smoke_test.py",
    "guarded_ppo_cross_platform_path_canonicalization_smoke_test.py",
    "guarded_ppo_checkpoint_sidecar_strict_contract_smoke_test.py",
    "guarded_ppo_dry_run_step0_alias_smoke_test.py",
)


def main() -> None:
    assert_helper_level_scripts(PURE_CHECKS)
    run_script_mains(
        "final_archive_guarded_ppo_lightweight_suite",
        PURE_CHECKS,
    )
    print("final_archive_guarded_ppo_lightweight_suite ok")


if __name__ == "__main__":
    main()
