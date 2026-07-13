from __future__ import annotations

from final_archive_suite_utils import run_script_mains


def main() -> None:
    run_script_mains(
        "final_archive_project_progress_suite",
        (
            "project_progress_active_echo_alignment_smoke_test.py",
            "project_progress_manual_120s_baseline_alignment_smoke_test.py",
            "project_progress_bc_demo_alignment_smoke_test.py",
            "project_progress_ppo_100k_alignment_smoke_test.py",
            "project_progress_guarded_ppo_alignment_smoke_test.py",
            "project_progress_guarded_ppo_results_alignment_smoke_test.py",
            "project_progress_beam_search_alignment_smoke_test.py",
            "project_progress_beam_search_calibration_alignment_smoke_test.py",
        ),
    )
    print("final_archive_project_progress_suite ok")


if __name__ == "__main__":
    main()
