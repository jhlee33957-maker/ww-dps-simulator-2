from __future__ import annotations

from final_archive_suite_utils import run_script_mains


def main() -> None:
    run_script_mains(
        "final_archive_beam_helper_suite",
        (
            "beam_search_plan_contract_smoke_test.py",
            "beam_search_clone_behavioral_parity_smoke_test.py",
            "beam_search_destination_bucket_order_independence_smoke_test.py",
            "beam_search_destination_accumulator_hot_path_smoke_test.py",
            "beam_search_accumulator_metrics_contract_smoke_test.py",
            "beam_search_compact_cli_output_smoke_test.py",
            "beam_search_terminal_replay_parity_smoke_test.py",
            "beam_search_horizon_comparison_guard_smoke_test.py",
        ),
    )
    print("final_archive_beam_helper_suite ok")


if __name__ == "__main__":
    main()
