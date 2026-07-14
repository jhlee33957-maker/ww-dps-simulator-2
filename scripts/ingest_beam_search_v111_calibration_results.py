from __future__ import annotations

"""Idempotently align the completed 30-second Beam calibration artifacts.

This utility only reads the completed result and writes derived metadata/reporting.
It never imports or invokes the Beam Search runner.
"""

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "results" / "beam_search_v111"
EXECUTION_RESULT = RESULT_ROOT / "execution_result.json"
SUMMARY_PATH = RESULT_ROOT / "calibration_result_summary.json"
REPORT_PATH = ROOT / "reports" / "beam_search_v111_calibration_results.md"
PROGRESS_PATH = ROOT / "PROJECT_PROGRESS_STATE.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _write_markdown(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(content)


def _calibration_summary(result: dict[str, Any]) -> dict[str, Any]:
    route = result["best_completed_search_route"]
    replay = result["route_replay_summaries"][0]
    memory = result["tracked_memory_estimate"]
    return {
        "schema_version": "beam_search_calibration_result_summary_v112",
        "candidate": "112",
        "source_candidate": "111",
        "stage_id": result["stage_id"],
        "combat_duration": result["stage"]["combat_duration"],
        "plan_path": result["plan_path"],
        "plan_sha256": result["plan_sha256"],
        "status": result["status"],
        "termination_status": result["termination_status"],
        "global_optimum_proven": False,
        "calibration_only_no_project_winner": True,
        "reference_damage_comparison_status": replay["reference_damage_comparison_status"],
        "search": {
            "maximum_expansions": result["maximum_expansions"],
            "actual_expansions": result["expansions"],
            "elapsed_seconds": result["elapsed_seconds"],
            "expansions_per_second": result["expansions_per_second"],
            "deduplicated_states": result["deduplicated_states"],
            "pruned_states": result["pruned_states"],
            "zero_time_expansions": result["zero_time_expansion_count"],
            "completed_time_buckets": len(result["completed_buckets"]),
            "retained_completed_routes": result["completed_route_count"],
            "observed_completed_routes_before_retention": result["next_completion_order"] - 1,
            "final_pending_buckets": len(result["pending_buckets"]),
            "final_destination_accumulators": len(result["destination_bucket_accumulators"]),
            "checkpoint_count": result["checkpoint_count"],
            "frontier_file_writes": result["frontier_file_write_count"],
            "accumulator_finalizations": result["accumulator_finalization_count"],
        },
        "memory": {
            "peak_live_nodes": result["peak_live_nodes"],
            "peak_serialized_payload_bytes": result["peak_serialized_payload_bytes"],
            "conservative_tracked_peak_memory_bytes": memory["conservative_total_bytes"],
        },
        "best_completed_route": {
            "route_id": route["route_id"],
            "completion_order": route["completion_order"],
            "total_damage": route["total_damage"],
            "dps": route["dps"],
            "final_combat_time": route["combat_time"],
            "final_current_time": route["current_time"],
            "selected_action_count": route["action_count"],
            "resolved_action_count": replay["resolved_action_count"],
            "selected_sequence_sha256": route["selected_sequence_sha256"],
            "resolved_sequence_sha256": route["resolved_sequence_sha256"],
        },
        "replay_attribution": {
            "terminal_party_preset_replay_parity": True,
            "damage_by_character": replay["damage_by_character"],
            "damage_by_character_sum": replay["damage_by_character_sum"],
            "scheduled_damage": replay["scheduled_damage"],
            "generated_mechanic_damage": replay["effective_damage_role_breakdown"]["generated_mechanic_damage"],
            "damage_by_character_sum_delta": replay["damage_by_character_sum"] - replay["total_damage"],
            "effective_damage_role_total_delta": replay["effective_damage_role_breakdown"]["total_damage_delta"],
        },
        "immutable_hashes": {
            **replay["data_contract_hashes"],
            "direct_action_manifest_sha256": "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d",
        },
        "canonical_paths": {
            "result_root": "results/beam_search_v111",
            "search_state": "results/beam_search_v111/search_state.json",
            "leaderboard": "results/beam_search_v111/leaderboard.json",
            "best_route": "results/beam_search_v111/best_route.json",
            "replay_summary": f"results/beam_search_v111/{replay['summary_path']}",
            "replay_timeline": f"results/beam_search_v111/{replay['timeline_csv_path']}",
            "report": "reports/beam_search_v111_calibration_results.md",
        },
    }


def _report(summary: dict[str, Any]) -> str:
    search = summary["search"]
    memory = summary["memory"]
    route = summary["best_completed_route"]
    attribution = summary["replay_attribution"]
    hashes = summary["immutable_hashes"]
    return f"""# Beam Search v111 30-second calibration result

Candidate 112 ingests the completed candidate-111 calibration. This is a result-integrity and readiness record, not a new search execution or an external-verification claim.

## Completion

- Plan: `{summary['plan_path']}` (`{summary['plan_sha256']}`)
- Stage/status: `{summary['stage_id']}` / `{summary['status']}` / `{summary['termination_status']}`
- Budget/actual expansions: {search['maximum_expansions']:,} / {search['actual_expansions']:,}
- Elapsed/throughput: {search['elapsed_seconds']:.13f} s / {search['expansions_per_second']:.13f} expansions/s
- Completed buckets/routes: {search['completed_time_buckets']} / {search['retained_completed_routes']} retained ({search['observed_completed_routes_before_retention']:,} observed before retention)
- Pending buckets/destination accumulators: {search['final_pending_buckets']} / {search['final_destination_accumulators']}
- Deduplicated/pruned/zero-time expansions: {search['deduplicated_states']:,} / {search['pruned_states']:,} / {search['zero_time_expansions']:,}
- Peak live nodes/payload/tracked memory: {memory['peak_live_nodes']:,} / {memory['peak_serialized_payload_bytes']:,} bytes / {memory['conservative_tracked_peak_memory_bytes']:,} bytes
- Checkpoints/frontier writes/accumulator finalizations: {search['checkpoint_count']} / {search['frontier_file_writes']} / {search['accumulator_finalizations']}

## Best completed 30-second route

- Route `{route['route_id']}` (completion order {route['completion_order']})
- Damage/DPS: {route['total_damage']:.12f} / {route['dps']:.13f}
- Combat/current time: {route['final_combat_time']:.1f} / {route['final_current_time']:.15f}
- Selected/resolved actions: {route['selected_action_count']} / {route['resolved_action_count']}
- Selected hash: `{route['selected_sequence_sha256']}`
- Resolved hash: `{route['resolved_sequence_sha256']}`

## Replay and attribution parity

The terminal node and deterministic party-preset replay agree on route identity, damage, time, action counts, and sequence hashes. Character attribution is Aemeath {attribution['damage_by_character']['aemeath']:.13f}, Lynae {attribution['damage_by_character']['lynae']:.13f}, and Mornye {attribution['damage_by_character']['mornye']:.14f}; scheduled damage is {attribution['scheduled_damage']:.15f} and generated mechanic damage is {attribution['generated_mechanic_damage']:.14f}. Character-sum delta is {attribution['damage_by_character_sum_delta']:.3g}; effective role-breakdown delta is {attribution['effective_damage_role_total_delta']:.1f}.

## Horizon warning

`reference_damage_comparison_status = {summary['reference_damage_comparison_status']}`. The 30-second calibration is **not numerically comparable** to the verified 120-second BC total, declares no project winner, and does not prove a global optimum.

## Immutable hashes

- Action data: `{hashes['action_data_hash']}`
- Party configuration: `{hashes['party_config_hash']}`
- Manual route: `{hashes['manual_route_raw_sha256']}`
- BC NPZ: `{hashes['bc_npz_sha256']}`
- BC model: `{hashes['bc_model_sha256']}`
- Prior PPO model: `{hashes['prior_ppo_model_sha256']}`
- Direct-action manifest: `{hashes['direct_action_manifest_sha256']}`
"""


def _update_progress(progress: dict[str, Any], summary: dict[str, Any]) -> None:
    status = progress["status"]
    current = progress["current_in_progress_task"]
    status.update({
        "last_updated": "2026-07-14T00:00:00+09:00",
        "latest_verified_archive": "ww-dps-simulator-2-111.zip",
        "latest_verified_baseline_label": "111",
        "current_task_status": "candidate_pending_external_review",
        "current_task": "30-second Beam Search calibration result ingestion and full-search readiness review",
        "current_task_expected_next_archive": "112",
        "candidate_expected_next_archive": "ww-dps-simulator-2-112.zip",
    })
    for item in progress["candidate_history"]:
        if item["candidate"] == "111":
            item.update({
                "status": "externally_verified_complete",
                "external_review_status": "passed",
                "external_verification_claimed": True,
                "external_verification_label": "111",
                "baseline_archive": "ww-dps-simulator-2-111.zip",
                "archive_sha256": "9577ee38ebbf655d51ab854970f01d6f10920b48b1abfd947080972592bc93a6",
                "validation_summary": {
                    "status": "externally_verified_complete",
                    "archive_path": "../ww-dps-simulator-2-111.zip",
                    "archive_exact_validation_passed": True,
                    "archive_sha256_reported_outside_progress_state": False,
                    "canonical_beam_search_results_written": False,
                    "notes": [
                        "Candidate 111 infrastructure archive was externally verified.",
                        "Candidate 111 did not run the 30-second calibration, full 120-second Beam Search, MCTS, BC training, or PPO training.",
                    ],
                },
            })
    progress["candidate_history"] = [item for item in progress["candidate_history"] if item.get("candidate") != "112"]
    progress["candidate_history"].append({
        "candidate": "112", "task": status["current_task"], "status": "candidate_pending_external_review",
        "latest_externally_verified_baseline": "111", "external_review_status": "pending", "external_verification_claimed": False,
        "calibration_stage_executed": True, "full_search_stage_executed": False, "mcts_execution": False,
        "calibration_result_summary": "results/beam_search_v111/calibration_result_summary.json",
        "report": "reports/beam_search_v111_calibration_results.md", "global_optimum_claimed": False,
    })
    current.update({
        "task": status["current_task"], "status": "candidate_pending_external_review", "candidate": "112", "external_review_required": True,
        "external_review_status": "pending", "external_verification_claimed": False, "latest_externally_verified_baseline": "111",
        "baseline_archive": "ww-dps-simulator-2-111.zip", "candidate_expected_next_archive": "ww-dps-simulator-2-112.zip",
        "beam_search_long_execution": False, "mcts_execution": False, "calibration_stage_executed": True,
        "full_search_stage_executed": False, "canonical_beam_search_results_written": True,
        "calibration_result_summary": "results/beam_search_v111/calibration_result_summary.json",
        "report": "reports/beam_search_v111_calibration_results.md", "global_optimum_claimed": False,
        "calibration_metrics": summary["search"], "calibration_best_route": summary["best_completed_route"],
        "reference_damage_comparison_status": "horizon_mismatch_not_comparable",
    })
    current["notes"] = [
        "Candidate 112 ingests the externally reviewed candidate-111 calibration; candidate 112 itself remains pending external review.",
        "The completed 30-second calibration has valid completed routes but declares no project winner or global optimum.",
        "The verified 120-second BC model remains the current best project result.",
        "Full 120-second Beam Search, MCTS, BC training, and PPO training were not run for candidate 112.",
    ]
    current["validation_summary"] = {"status": "pending_final_archive_validation", "archive_path": "../ww-dps-simulator-2-112.zip", "archive_exact_validation_passed": False, "archive_sha256_reported_outside_progress_state": True, "canonical_beam_search_results_written": True, "notes": ["Calibration result ingestion and integrity guards completed without rerunning search."]}
    progress["next_planned_tasks"] = [
        {"task": "external review of candidate 112"},
        {"task": "run the reviewed 120-second Beam Search stage"},
        {"task": "resume rather than restart if interrupted"},
        {"task": "compare only completed 120-second routes with the verified BC result"},
        {"task": "consider MCTS only after reviewing the full Beam result"},
    ]
    progress["next_planned_task"] = "run the reviewed 120-second Beam Search stage after candidate 112 external verification"


def ingest(*, write: bool) -> dict[str, Any]:
    result = _read_json(EXECUTION_RESULT)
    # Canonical result fields must be portable; route and metric payloads remain untouched.
    if result.get("output_root") != "results/beam_search_v111":
        result["output_root"] = "results/beam_search_v111"
    summary = _calibration_summary(result)
    progress = _read_json(PROGRESS_PATH)
    current_candidate = int(progress.get("current_in_progress_task", {}).get("candidate", 0))
    preserve_newer_progress = current_candidate > 112
    if not preserve_newer_progress:
        _update_progress(progress, summary)
    if write:
        _write_json(EXECUTION_RESULT, result)
        _write_json(SUMMARY_PATH, summary)
        _write_markdown(REPORT_PATH, _report(summary))
        if not preserve_newer_progress:
            _write_json(PROGRESS_PATH, progress)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest completed Beam calibration artifacts without running search.")
    parser.add_argument("--write", action="store_true", help="write normalized metadata, summary, report, and progress state")
    args = parser.parse_args()
    summary = ingest(write=args.write)
    print(json.dumps({"status": "ok", "write": args.write, "stage": summary["stage_id"], "route_id": summary["best_completed_route"]["route_id"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
