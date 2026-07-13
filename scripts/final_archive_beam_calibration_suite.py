from __future__ import annotations

from final_archive_suite_utils import run_script_mains


def main() -> None:
    run_script_mains(
        "final_archive_beam_calibration_suite",
        (
            "beam_search_calibration_result_integrity_smoke_test.py",
            "beam_search_calibration_ingestion_idempotence_smoke_test.py",
            "beam_search_calibration_artifact_path_smoke_test.py",
            "beam_search_calibration_report_format_smoke_test.py",
            "progress_dashboard_beam_calibration_alignment_smoke_test.py",
            "progress_dashboard_beam_calibration_render_smoke_test.py",
        ),
    )
    print("final_archive_beam_calibration_suite ok")


if __name__ == "__main__":
    main()
