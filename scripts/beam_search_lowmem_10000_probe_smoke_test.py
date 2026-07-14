from __future__ import annotations

import json
import hashlib
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import LOWMEM_32GB_PLAN_PATH, load_plan
from search.beam_search import BeamSearchRunner


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


def main() -> int:
    process_started = time.perf_counter()
    plan = load_plan(LOWMEM_32GB_PLAN_PATH)
    stage = dict(plan["stages"][0], maximum_expansions=10000)
    canonical = ROOT / "results/beam_search_v113_lowmem_32gb"
    canonical_before = tree_digest(canonical)
    temporary = Path(tempfile.mkdtemp(prefix="beam-lowmem-10000-probe-"))
    output = temporary / "probe"
    try:
        result = BeamSearchRunner(plan=plan, stage=stage, plan_path=LOWMEM_32GB_PLAN_PATH, output_root=output).run()
        assert result["expansions"] == 10000
        assert result["termination_status"] == "expansion_budget_exhausted"
        assert result["tracked_memory_estimate"]["conservative_total_bytes"] < stage["memory_budget_bytes"]
        assert result["peak_process_rss_bytes"] < stage["memory_budget_bytes"]
        accumulators = result["destination_bucket_accumulators"]
        accumulator_metrics = result["destination_bucket_accumulator_metrics"]
        spill_entries = [entry for accumulator in accumulators.values() for entry in accumulator.get("spill_chunks", [])]
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
            "search_runtime_seconds": result["elapsed_seconds"],
            "expansions_per_second": result["expansions_per_second"],
            "expansions": result["expansions"],
            "peak_live_nodes": result["peak_live_nodes"],
            "peak_tracked_memory_bytes": result["tracked_memory_estimate"]["conservative_total_bytes"],
            "peak_process_rss_bytes": result["peak_process_rss_bytes"],
            "compact_manifest_bytes": (output / "search_state.json").stat().st_size,
            "spill_chunk_count": len(spill_entries),
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
        }
        assert metrics["spill_chunk_count"] > 0
        assert metrics["maximum_spill_serialization_buffer_bytes"] < 1024 * 1024
        assert metrics["maximum_spill_restore_buffer_bytes"] < 1024 * 1024
        assert tree_digest(canonical) == canonical_before
        cleanup_started = time.perf_counter()
        shutil.rmtree(output, ignore_errors=False)
        metrics["cleanup_runtime_seconds"] = time.perf_counter() - cleanup_started
        metrics["cleanup_completed"] = not output.exists()
        metrics["total_process_runtime_seconds"] = time.perf_counter() - process_started
        assert metrics["cleanup_completed"]
        print("LOWMEM_PROBE_METRICS=" + json.dumps(metrics, sort_keys=True), flush=True)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=False)
    print("beam_search_lowmem_10000_probe_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
