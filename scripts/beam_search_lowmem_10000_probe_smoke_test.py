from __future__ import annotations

import argparse
import json
import hashlib
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import (
    LOWMEM_32GB_PLAN_PATH,
    STREAMING_ACCUMULATOR_SPILL_FORMAT,
    load_plan,
    resolve_accumulator_spill_format,
    sha256_file,
)
from search.beam_search import BeamSearchRunner
from search.beam_spill import STREAMING_CHUNK_SCHEMA
from search.beam_state import clone_simulation_for_search, future_state_fingerprint


PROTECTED_HISTORICAL_RESULTS_ROOT = (ROOT / "results").resolve()
PROTECTED_HISTORICAL_SUMMARY = PROTECTED_HISTORICAL_RESULTS_ROOT / "beam_search_v114_lowmem_10000_probe_summary.json"
EXPECTED_HISTORICAL_SUMMARY_SHA256 = "61e789992660dd49e9183c7f4e7306ceafb52d7eff5a2ee79ac24292bb78ecff"


def directory_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def tree_digest(root: Path) -> str | None:
    if not root.exists():
        return None
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        with path.open("rb") as file:
            for block in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def resolve_summary_output(path: Path | None) -> Path | None:
    if path is None:
        return None
    resolved = (path if path.is_absolute() else ROOT / path).resolve()
    if resolved == PROTECTED_HISTORICAL_RESULTS_ROOT or PROTECTED_HISTORICAL_RESULTS_ROOT in resolved.parents:
        raise ValueError("--summary-output must not target protected historical results")
    return resolved


def write_diagnostic_summary(path: Path, *, plan: dict, metrics: dict) -> None:
    summary = {
        "schema_version": "beam_search_lowmem_10000_probe_diagnostic",
        "candidate": plan.get("candidate"),
        **metrics,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")
    temporary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary_path, path)


def historical_summary_state() -> tuple[str, int, int]:
    assert PROTECTED_HISTORICAL_SUMMARY.is_file(), PROTECTED_HISTORICAL_SUMMARY
    stat = PROTECTED_HISTORICAL_SUMMARY.stat()
    digest = sha256_file(PROTECTED_HISTORICAL_SUMMARY)
    assert digest == EXPECTED_HISTORICAL_SUMMARY_SHA256, digest
    return digest, stat.st_size, stat.st_mtime_ns


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=LOWMEM_32GB_PLAN_PATH)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args(argv)
    plan_path = args.plan if args.plan.is_absolute() else ROOT / args.plan
    summary_output = resolve_summary_output(args.summary_output)
    historical_summary_before = historical_summary_state()
    process_started = time.perf_counter()
    plan = load_plan(plan_path)
    stage = dict(plan["stages"][0], maximum_expansions=10000)
    resolved_spill_format = resolve_accumulator_spill_format(stage)
    canonical = ROOT / str(plan["output_contract"]["canonical_output_root"])
    canonical_before = tree_digest(canonical)
    temporary = Path(tempfile.mkdtemp(prefix="beam-lowmem-10000-probe-"))
    output = temporary / "probe"
    try:
        runner = BeamSearchRunner(plan=plan, stage=stage, plan_path=plan_path, output_root=output)
        if plan.get("candidate") == 114:
            guard = runner._create_simulation()
            assert guard.execute_action("swap_to_mornye")
            assert guard.execute_action("swap_to_lynae")
            assert not guard.execute_action("swap_to_aemeath")
            assert not guard.execute_action("swap_to_mornye")
            clone = clone_simulation_for_search(guard)
            assert clone.state.cooldowns == guard.state.cooldowns
            assert future_state_fingerprint(clone) == future_state_fingerprint(guard)
        result = runner.run()
        assert result["expansions"] == 10000
        assert result["termination_status"] == "expansion_budget_exhausted"
        assert result["tracked_memory_estimate"]["conservative_total_bytes"] < stage["memory_budget_bytes"]
        assert result["peak_process_rss_bytes"] < stage["memory_budget_bytes"]
        accumulators = result["destination_bucket_accumulators"]
        accumulator_metrics = result["destination_bucket_accumulator_metrics"]
        spill_entries = [entry for accumulator in accumulators.values() for entry in accumulator.get("spill_chunks", [])]
        if plan.get("candidate") == 114:
            assert stage["stage_id"] == "full_120s_lowmem_32gb_v114"
            assert resolved_spill_format == STREAMING_ACCUMULATOR_SPILL_FORMAT
            assert result["accumulator_spill_format"] == STREAMING_ACCUMULATOR_SPILL_FORMAT
            assert result["accumulator_spill_chunk_schema"] == STREAMING_CHUNK_SCHEMA
            assert all(entry.get("schema_version") == STREAMING_CHUNK_SCHEMA for entry in spill_entries)
        deterministic_payload = {
            "expansions": result["expansions"],
            "termination_status": result["termination_status"],
            "next_node_id": result["next_node_id"],
            "deduplicated_states": result["deduplicated_states"],
            "pruned_states": result["pruned_states"],
            "best_partial_future_fingerprint": (result.get("best_partial_frontier_node") or {}).get("future_fingerprint"),
            "best_partial_total_damage": (result.get("best_partial_frontier_node") or {}).get("total_damage"),
            "spill_chunks": [
                {
                    "schema_version": entry["schema_version"],
                    "bucket_index": entry["bucket_index"],
                    "chunk_index": entry["chunk_index"],
                    "sha256": entry["sha256"],
                    "candidate_count": entry["candidate_count"],
                    "compressed_bytes": entry["compressed_bytes"],
                }
                for entry in spill_entries
            ],
        }
        deterministic_result_sha256 = hashlib.sha256(
            json.dumps(deterministic_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        lifecycle = result["accumulator_lifecycle_metrics"]
        phases = result["phase_timing_metrics"]
        metrics = {
            "plan_path": plan_path.relative_to(ROOT).as_posix(),
            "plan_sha256": sha256_file(plan_path),
            "stage_id": stage["stage_id"],
            "resolved_accumulator_spill_format": resolved_spill_format,
            "accumulator_spill_chunk_schema": result["accumulator_spill_chunk_schema"],
            "search_runtime_seconds": result["elapsed_seconds"],
            "expansions_per_second": result["expansions_per_second"],
            "expansions": result["expansions"],
            "peak_live_nodes": result["peak_live_nodes"],
            "peak_tracked_memory_bytes": result["tracked_memory_estimate"]["conservative_total_bytes"],
            "peak_process_rss_bytes": result["peak_process_rss_bytes"],
            "compact_manifest_bytes": (output / "search_state.json").stat().st_size,
            "spill_chunk_count": len(spill_entries),
            "spill_chunk_sha256s": [entry["sha256"] for entry in spill_entries],
            "accumulator_spill_bytes": sum(int(entry["compressed_bytes"]) for entry in spill_entries),
            "accumulator_directory_bytes": directory_bytes(output / "frontier/accumulators"),
            "maximum_spill_chunk_uncompressed_bytes": max((int(entry.get("uncompressed_bytes", 0)) for entry in spill_entries), default=0),
            "maximum_spill_serialization_buffer_bytes": max((int(item.get("peak_spill_serialization_buffer_bytes", 0)) for item in accumulator_metrics.values()), default=0),
            "maximum_spill_restore_buffer_bytes": max((int(item.get("peak_spill_restore_buffer_bytes", 0)) for item in accumulator_metrics.values()), default=0),
            "maximum_finalization_unique_set_bytes": max((int(item.get("peak_finalization_unique_set_bytes", 0)) for item in accumulator_metrics.values()), default=0),
            "maximum_final_sort_list_bytes": max((int(item.get("peak_final_sort_list_bytes", 0)) for item in accumulator_metrics.values()), default=0),
            "checkpoint_count": result["checkpoint_count"],
            "spill_write_count": int(lifecycle["spill_write_count"]),
            "spill_write_seconds": float(lifecycle["spill_write_seconds"]),
            "spill_sha_validation_count": int(lifecycle["spill_sha_validation_count"]),
            "spill_sha_validation_seconds": float(lifecycle["spill_sha_validation_seconds"]),
            "spill_restore_pass_count": int(lifecycle["spill_restore_pass_count"]),
            "spill_restore_nodes_streamed": int(lifecycle["spill_restore_nodes_streamed"]),
            "spill_restore_seconds": float(lifecycle["spill_restore_seconds"]),
            "accumulator_finalization_count": int(lifecycle["full_accumulator_finalization_count"]),
            "accumulator_finalization_seconds": float(lifecycle["accumulator_finalization_seconds"]),
            "duplicate_merge_seconds": float(lifecycle["duplicate_merge_seconds"]),
            "retained_selection_seconds": float(lifecycle["retained_selection_seconds"]),
            "checkpoint_manifest_generation_count": int(phases["checkpoint_manifest_generation_count"]),
            "forced_checkpoint_manifest_generation_count": int(phases["forced_checkpoint_manifest_generation_count"]),
            "checkpoint_manifest_generation_seconds": float(phases["checkpoint_manifest_generation_seconds"]),
            "pending_frontier_serialization_seconds": float(phases["pending_frontier_serialization_seconds"]),
            "route_store_compaction_seconds": float(phases["route_store_compaction_seconds"]),
            "result_creation_seconds": float(phases["result_creation_seconds"]),
            "best_partial_future_fingerprint": deterministic_payload["best_partial_future_fingerprint"],
            "best_partial_total_damage": deterministic_payload["best_partial_total_damage"],
            "deterministic_result_sha256": deterministic_result_sha256,
            "v114_zero_time_loop_guard": plan.get("candidate") != 114 or True,
            "v114_target_reentry_masks": plan.get("candidate") != 114 or True,
            "v114_clone_restore_swap_cooldown_parity": plan.get("candidate") != 114 or True,
        }
        assert metrics["spill_chunk_count"] > 0
        if plan.get("candidate") == 114:
            assert metrics["maximum_spill_chunk_uncompressed_bytes"] > 0
            assert metrics["maximum_spill_serialization_buffer_bytes"] > 0
            assert metrics["maximum_spill_restore_buffer_bytes"] > 0
        assert metrics["maximum_spill_serialization_buffer_bytes"] < 1024 * 1024
        assert metrics["maximum_spill_restore_buffer_bytes"] < 1024 * 1024
        metrics["canonical_output_mutated"] = tree_digest(canonical) != canonical_before
        assert metrics["canonical_output_mutated"] is False
        cleanup_started = time.perf_counter()
        shutil.rmtree(output, ignore_errors=False)
        metrics["cleanup_runtime_seconds"] = time.perf_counter() - cleanup_started
        metrics["cleanup_completed"] = not output.exists()
        metrics["total_process_runtime_seconds"] = time.perf_counter() - process_started
        metrics["normal_process_exit"] = True
        assert metrics["cleanup_completed"]
        if summary_output is not None:
            write_diagnostic_summary(summary_output, plan=plan, metrics=metrics)
        assert historical_summary_state() == historical_summary_before
        print("LOWMEM_PROBE_METRICS=" + json.dumps(metrics, sort_keys=True), flush=True)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=False)
    print("beam_search_lowmem_10000_probe_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
