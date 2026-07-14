from __future__ import annotations

import argparse
import math
import hashlib
import json
import os
import time
import ctypes
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from simulator.simulation import Simulation

from search.beam_plan import (
    DEFAULT_PLAN_PATH,
    FORBIDDEN_64GB_OUTPUT_ROOT,
    LOWMEM_32GB_SCHEMA,
    STREAMING_ACCUMULATOR_SPILL_FORMAT,
    V114_LOWMEM_32GB_SCHEMA,
    ROOT,
    load_plan,
    resolve_plan_data_hashes,
    resolve_accumulator_spill_format,
    sha256_file,
    stage_by_id,
    validate_plan,
)
from search.beam_reporting import historical_verified_bc_reference, load_project_comparison_incumbent, replay_selected_route_to_files, select_damage_only_winner, verified_bc_incumbent_manifest
from search.beam_performance import migrate_prior_accounting, performance_accounting
from search.beam_resume_extension import extension_stage_compatible, validate_hash_pinned_extension
from search.beam_spill import STREAMING_CHUNK_SCHEMA, iter_accumulator_chunk_nodes, write_accumulator_chunk_streaming
from search.beam_state import (
    BeamNode,
    clone_simulation_for_search,
    make_node,
    read_json_gz,
    restore_simulation_from_state,
    sequence_sha256,
    write_json_gz,
)


CANONICAL_RESULTS_ROOT = ROOT / "results" / "beam_search_v111"
SMOKE_STAGE_ID = "smoke_3s"
TERMINATION_STATUSES = {
    "completed_search",
    "expansion_budget_exhausted",
    "wall_clock_budget_exhausted",
    "memory_budget_exhausted",
    "frontier_exhausted_without_complete_route",
    "interrupted_resumable",
    "contract_failure",
}
ACCUMULATOR_LIFECYCLE_METRIC_KEYS = (
    "spill_write_count",
    "spill_write_seconds",
    "spill_sha_validation_count",
    "spill_sha_validation_seconds",
    "spill_restore_pass_count",
    "spill_restore_nodes_streamed",
    "spill_restore_seconds",
    "full_accumulator_finalization_count",
    "accumulator_finalization_seconds",
    "duplicate_merge_seconds",
    "retained_selection_seconds",
)


class DestinationBucketAccumulator:
    schema_version = "beam_search_destination_bucket_accumulator_v111"
    chunk_schema_version = "beam_search_destination_bucket_accumulator_chunk_v111"

    def __init__(
        self,
        *,
        bucket_index: int,
        stage: dict[str, Any],
        max_unique_fingerprints: int | None = None,
        spill_root: Path | None = None,
        output_root: Path | None = None,
        plan_sha256: str = "unbound_test_plan",
        stage_contract_sha256: str | None = None,
    ) -> None:
        self.bucket_index = int(bucket_index)
        self.stage = dict(stage)
        self.max_unique_fingerprints = int(max_unique_fingerprints or _accumulator_unique_bound(stage))
        self.spill_root = spill_root
        self.output_root = output_root
        self.plan_sha256 = str(plan_sha256)
        self.stage_contract_sha256 = stage_contract_sha256 or _spill_stage_contract_sha256(stage)
        self.accumulator_spill_format = resolve_accumulator_spill_format(self.stage)
        self.streaming_spill = self.accumulator_spill_format == STREAMING_ACCUMULATOR_SPILL_FORMAT
        self.best_by_fingerprint: dict[str, BeamNode] = {}
        self.spill_chunks: list[dict[str, Any]] = []
        self.candidates_seen = 0
        self.hot_path_exact_fingerprint_duplicates = 0
        self.hot_path_better_duplicate_replacements = 0
        self.spilled_candidate_count = 0
        self.spilled_unique_fingerprint_count = 0
        self.spilled_bytes = 0
        self.retained_set_finalization_count = 0
        self.full_retained_set_scan_count = 0
        self.peak_spill_serialization_buffer_bytes = 0
        self.peak_spill_restore_buffer_bytes = 0
        self.peak_spill_chunk_uncompressed_bytes = 0
        self.peak_finalization_unique_node_count = 0
        self.peak_finalization_unique_set_bytes = 0
        self.peak_final_sort_node_count = 0
        self.peak_final_sort_list_bytes = 0
        self.spill_write_count = 0
        self.spill_write_seconds = 0.0
        self.spill_sha_validation_count = 0
        self.spill_sha_validation_seconds = 0.0
        self.spill_restore_pass_count = 0
        self.spill_restore_nodes_streamed = 0
        self.spill_restore_seconds = 0.0
        self.full_accumulator_finalization_count = 0
        self.accumulator_finalization_seconds = 0.0
        self.duplicate_merge_seconds = 0.0
        self.retained_selection_seconds = 0.0
        self.finalization_needed = True
        self._finalized_cache: dict[str, Any] | None = None

    def add(self, node: BeamNode) -> dict[str, int]:
        self._finalized_cache = None
        self.finalization_needed = True
        self.candidates_seen += 1
        existing = self.best_by_fingerprint.get(node.future_fingerprint)
        result = {"duplicate": 0, "replacement": 0}
        if existing is None:
            if len(self.best_by_fingerprint) >= self.max_unique_fingerprints:
                self.spill_current_chunk()
            self.best_by_fingerprint[node.future_fingerprint] = node
            return result
        self.hot_path_exact_fingerprint_duplicates += 1
        result["duplicate"] = 1
        if _node_order_key(node) < _node_order_key(existing):
            self.best_by_fingerprint[node.future_fingerprint] = node
            self.hot_path_better_duplicate_replacements += 1
            result["replacement"] = 1
        return result

    def merge(self, other: "DestinationBucketAccumulator") -> None:
        original_seen = self.candidates_seen
        for node in sorted(other.iter_unique_nodes(), key=_node_order_key):
            self.add(node)
        self.candidates_seen = original_seen + other.candidates_seen
        self.hot_path_exact_fingerprint_duplicates += other.hot_path_exact_fingerprint_duplicates
        self.hot_path_better_duplicate_replacements += other.hot_path_better_duplicate_replacements

    def retained_nodes(self) -> list[BeamNode]:
        return self.finalize_retention()["retained"]

    def metrics(self) -> dict[str, Any]:
        return self.finalize_retention()["metrics"]

    def finalize_retention(self) -> dict[str, Any]:
        if self._finalized_cache is not None:
            return self._finalized_cache
        finalization_started = time.perf_counter()
        self.retained_set_finalization_count += 1
        self.full_retained_set_scan_count += 1
        self.full_accumulator_finalization_count += 1
        best_by_fingerprint: dict[str, BeamNode] = {}
        better_duplicate_replacements = int(self.hot_path_better_duplicate_replacements)
        merge_started = time.perf_counter()
        for node in self.iter_unique_nodes():
            existing = best_by_fingerprint.get(node.future_fingerprint)
            if existing is None:
                best_by_fingerprint[node.future_fingerprint] = node
            elif _node_order_key(node) < _node_order_key(existing):
                best_by_fingerprint[node.future_fingerprint] = node
                better_duplicate_replacements += 1
        self.duplicate_merge_seconds += time.perf_counter() - merge_started
        unique_count = len(best_by_fingerprint)
        unique_payload_bytes = sum(max(int(node.payload_size_bytes), 1) for node in best_by_fingerprint.values())
        self.peak_finalization_unique_node_count = max(self.peak_finalization_unique_node_count, unique_count)
        self.peak_finalization_unique_set_bytes = max(
            self.peak_finalization_unique_set_bytes,
            unique_payload_bytes + unique_count * 128,
        )
        self.peak_final_sort_node_count = max(self.peak_final_sort_node_count, unique_count)
        self.peak_final_sort_list_bytes = max(self.peak_final_sort_list_bytes, unique_count * 8)
        selection_started = time.perf_counter()
        selected = _select_retained_unique(best_by_fingerprint.values(), self.stage)
        self.retained_selection_seconds += time.perf_counter() - selection_started
        exact_duplicates = max(0, int(self.candidates_seen) - unique_count)
        final_rejected = int(selected["metrics"]["final_rejected_count"])
        if int(self.candidates_seen) != exact_duplicates + unique_count:
            raise AssertionError("Destination accumulator candidate conservation failed")
        if unique_count != int(selected["metrics"]["final_retained_count"]) + final_rejected:
            raise AssertionError("Destination accumulator final-retention conservation failed")
        metrics = {
            "schema_version": "beam_search_destination_bucket_accumulator_metrics_v111",
            "bucket_index": self.bucket_index,
            "candidates_seen": self.candidates_seen,
            "unique_fingerprint_count": unique_count,
            "max_unique_fingerprints": self.max_unique_fingerprints,
            "exact_fingerprint_duplicates": exact_duplicates,
            "better_duplicate_replacements": better_duplicate_replacements,
            "hot_path_exact_fingerprint_duplicates": self.hot_path_exact_fingerprint_duplicates,
            "hot_path_better_duplicate_replacements": self.hot_path_better_duplicate_replacements,
            "spilled_candidates": self.spilled_candidate_count,
            "spilled_unique_fingerprints": self.spilled_unique_fingerprint_count,
            "spill_chunk_count": len(self.spill_chunks),
            "spill_bytes": self.spilled_bytes,
            "retained_set_finalization_count": self.retained_set_finalization_count,
            "full_retained_set_scan_count": self.full_retained_set_scan_count,
            "peak_spill_serialization_buffer_bytes": self.peak_spill_serialization_buffer_bytes,
            "peak_spill_restore_buffer_bytes": self.peak_spill_restore_buffer_bytes,
            "peak_spill_chunk_uncompressed_bytes": self.peak_spill_chunk_uncompressed_bytes,
            "peak_finalization_unique_node_count": self.peak_finalization_unique_node_count,
            "peak_finalization_unique_set_bytes": self.peak_finalization_unique_set_bytes,
            "peak_final_sort_node_count": self.peak_final_sort_node_count,
            "peak_final_sort_list_bytes": self.peak_final_sort_list_bytes,
            **self._lifecycle_count_metrics(),
            **{f"selection_{key}": value for key, value in selected["metrics"].items()},
        }
        metrics.update(
            {
                "final_retained_count": selected["metrics"]["final_retained_count"],
                "final_rejected_count": final_rejected,
                "rejected_by_global_only_region": selected["metrics"]["candidates_outside_global_quota"],
                "rejected_by_diversity_key_cap": selected["metrics"]["candidates_rejected_by_diversity_key_cap"],
                "rejected_because_diversity_quota_filled": selected["metrics"]["candidates_rejected_by_diversity_quota"],
                "rejected_by_final_beam_width": selected["metrics"]["candidates_rejected_by_final_beam_width"],
            }
        )
        self.accumulator_finalization_seconds += time.perf_counter() - finalization_started
        metrics.update(self._lifecycle_count_metrics())
        self.finalization_needed = False
        self._finalized_cache = {"retained": selected["retained"], "metrics": metrics}
        return self._finalized_cache

    def spill_current_chunk(self) -> dict[str, Any] | None:
        if not self.best_by_fingerprint:
            return None
        if self.spill_root is None:
            return None
        spill_started = time.perf_counter()
        nodes = sorted(self.best_by_fingerprint.values(), key=_node_order_key)
        chunk_index = len(self.spill_chunks)
        suffix = ".jsonl.gz" if self.streaming_spill else ".json.gz"
        path = self.spill_root / f"accumulator_bucket_{self.bucket_index:06d}_chunk_{chunk_index:06d}{suffix}"
        if self.streaming_spill:
            entry = write_accumulator_chunk_streaming(
                path,
                nodes,
                bucket_index=self.bucket_index,
                chunk_index=chunk_index,
                plan_sha256=self.plan_sha256,
                stage_id=str(self.stage["stage_id"]),
                stage_contract_sha256=self.stage_contract_sha256,
            )
            entry["path"] = _portable_spill_path(path, self.output_root)
            self.peak_spill_serialization_buffer_bytes = max(
                self.peak_spill_serialization_buffer_bytes,
                int(entry["max_serialization_buffer_bytes"]),
            )
            self.peak_spill_chunk_uncompressed_bytes = max(
                self.peak_spill_chunk_uncompressed_bytes,
                int(entry["uncompressed_bytes"]),
            )
        else:
            payload = {
                "schema_version": self.chunk_schema_version,
                "bucket_index": self.bucket_index,
                "chunk_index": chunk_index,
                "nodes": [node.to_json() for node in nodes],
            }
            sha = write_json_gz(path, payload)
            entry = {
                "schema_version": self.chunk_schema_version,
                "bucket_index": self.bucket_index,
                "chunk_index": chunk_index,
                "path": _path_text(path),
                "sha256": sha,
                "candidate_count": len(nodes),
                "unique_fingerprint_count": len(nodes),
                "node_ids": [node.node_id for node in nodes],
                "compressed_bytes": path.stat().st_size,
            }
        self._finalized_cache = None
        self.finalization_needed = True
        self.spill_chunks.append(entry)
        self.spilled_candidate_count += len(nodes)
        self.spilled_unique_fingerprint_count += len(nodes)
        self.spilled_bytes += int(entry["compressed_bytes"])
        self.best_by_fingerprint.clear()
        self.spill_write_count += 1
        self.spill_write_seconds += time.perf_counter() - spill_started
        return entry

    def iter_unique_nodes(self) -> Iterator[BeamNode]:
        for chunk in self.spill_chunks:
            path = _resolve_stored_path(str(chunk["path"]), self.output_root)
            if chunk.get("schema_version") == STREAMING_CHUNK_SCHEMA:
                restore_metrics: dict[str, Any] = {}
                yield from iter_accumulator_chunk_nodes(
                    path,
                    chunk,
                    expected_plan_sha256=str(chunk.get("plan_sha256", self.plan_sha256)),
                    expected_stage_id=str(chunk.get("stage_id", self.stage["stage_id"])),
                    expected_stage_contract_sha256=str(chunk.get("stage_contract_sha256", self.stage_contract_sha256)),
                    metrics=restore_metrics,
                )
                self.peak_spill_restore_buffer_bytes = max(
                    self.peak_spill_restore_buffer_bytes,
                    int(restore_metrics.get("max_restore_buffer_bytes", 0)),
                )
                self.spill_sha_validation_count += int(restore_metrics.get("sha_validation_count", 0))
                self.spill_sha_validation_seconds += float(restore_metrics.get("sha_validation_seconds", 0.0))
                self.spill_restore_pass_count += int(restore_metrics.get("restore_pass_count", 0))
                self.spill_restore_nodes_streamed += int(restore_metrics.get("restore_node_count", 0))
                self.spill_restore_seconds += float(restore_metrics.get("restore_seconds", 0.0))
                continue
            restore_started = time.perf_counter()
            payload = read_json_gz(path, str(chunk["sha256"]))
            self.spill_sha_validation_count += 1
            self.spill_restore_pass_count += 1
            if payload.get("schema_version") != self.chunk_schema_version:
                raise ValueError(f"Unsupported destination accumulator chunk schema: {payload.get('schema_version')!r}")
            for item in payload.get("nodes", []):
                self.spill_restore_nodes_streamed += 1
                yield BeamNode.from_json(item)
            self.spill_restore_seconds += time.perf_counter() - restore_started
        yield from self.best_by_fingerprint.values()

    def node_ids(self) -> list[int]:
        ids = [node.node_id for node in self.best_by_fingerprint.values()]
        for chunk in self.spill_chunks:
            ids.extend(int(node_id) for node_id in chunk.get("node_ids", []))
        return ids

    def manifest(self, *, retained_view_count: int | None = None, force_spill: bool = False) -> dict[str, Any]:
        if force_spill:
            self.spill_current_chunk()
        return {
            "schema_version": self.schema_version,
            "bucket_index": self.bucket_index,
            "accumulator_spill_format": self.accumulator_spill_format,
            "accumulator_spill_chunk_schema": (
                STREAMING_CHUNK_SCHEMA if self.streaming_spill else self.chunk_schema_version
            ),
            "max_unique_fingerprints": self.max_unique_fingerprints,
            "candidates_seen": self.candidates_seen,
            "current_unique_fingerprint_count": len(self.best_by_fingerprint),
            "spill_chunk_count": len(self.spill_chunks),
            "spill_chunks": list(self.spill_chunks),
            "spilled_candidates": self.spilled_candidate_count,
            "spilled_unique_fingerprints": self.spilled_unique_fingerprint_count,
            "spill_bytes": self.spilled_bytes,
            "retained_view_count": retained_view_count,
            "hot_path_exact_fingerprint_duplicates": self.hot_path_exact_fingerprint_duplicates,
            "hot_path_better_duplicate_replacements": self.hot_path_better_duplicate_replacements,
            "retained_set_finalization_count": self.retained_set_finalization_count,
            "full_retained_set_scan_count": self.full_retained_set_scan_count,
            "peak_spill_serialization_buffer_bytes": self.peak_spill_serialization_buffer_bytes,
            "peak_spill_restore_buffer_bytes": self.peak_spill_restore_buffer_bytes,
            "peak_spill_chunk_uncompressed_bytes": self.peak_spill_chunk_uncompressed_bytes,
            "peak_finalization_unique_node_count": self.peak_finalization_unique_node_count,
            "peak_finalization_unique_set_bytes": self.peak_finalization_unique_set_bytes,
            "peak_final_sort_node_count": self.peak_final_sort_node_count,
            "peak_final_sort_list_bytes": self.peak_final_sort_list_bytes,
            "finalization_needed": self.finalization_needed,
            **self._timing_metrics(),
        }

    def cheap_metrics(self) -> dict[str, Any]:
        """Return checkpoint-safe counters without restoring or finalizing spill chunks."""
        return {
            "schema_version": "beam_search_destination_bucket_accumulator_metrics_snapshot_v113",
            "bucket_index": self.bucket_index,
            "candidates_seen": self.candidates_seen,
            "current_unique_fingerprint_count": len(self.best_by_fingerprint),
            "spilled_candidates": self.spilled_candidate_count,
            "spilled_unique_fingerprints": self.spilled_unique_fingerprint_count,
            "spill_chunk_count": len(self.spill_chunks),
            "spill_bytes": self.spilled_bytes,
            "hot_path_exact_fingerprint_duplicates": self.hot_path_exact_fingerprint_duplicates,
            "hot_path_better_duplicate_replacements": self.hot_path_better_duplicate_replacements,
            "retained_set_finalization_count": self.retained_set_finalization_count,
            "full_retained_set_scan_count": self.full_retained_set_scan_count,
            "peak_spill_serialization_buffer_bytes": self.peak_spill_serialization_buffer_bytes,
            "peak_spill_restore_buffer_bytes": self.peak_spill_restore_buffer_bytes,
            "peak_spill_chunk_uncompressed_bytes": self.peak_spill_chunk_uncompressed_bytes,
            "peak_finalization_unique_node_count": self.peak_finalization_unique_node_count,
            "peak_finalization_unique_set_bytes": self.peak_finalization_unique_set_bytes,
            "peak_final_sort_node_count": self.peak_final_sort_node_count,
            "peak_final_sort_list_bytes": self.peak_final_sort_list_bytes,
            "finalization_needed": self.finalization_needed,
            **self._timing_metrics(),
        }

    def _timing_metrics(self) -> dict[str, Any]:
        return {
            "spill_write_count": self.spill_write_count,
            "spill_write_seconds": self.spill_write_seconds,
            "spill_sha_validation_count": self.spill_sha_validation_count,
            "spill_sha_validation_seconds": self.spill_sha_validation_seconds,
            "spill_restore_pass_count": self.spill_restore_pass_count,
            "spill_restore_nodes_streamed": self.spill_restore_nodes_streamed,
            "spill_restore_seconds": self.spill_restore_seconds,
            "full_accumulator_finalization_count": self.full_accumulator_finalization_count,
            "accumulator_finalization_seconds": self.accumulator_finalization_seconds,
            "duplicate_merge_seconds": self.duplicate_merge_seconds,
            "retained_selection_seconds": self.retained_selection_seconds,
        }

    def _lifecycle_count_metrics(self) -> dict[str, int]:
        return {
            key: int(value)
            for key, value in self._timing_metrics().items()
            if not key.endswith("_seconds")
        }

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bucket_index": self.bucket_index,
            "accumulator_spill_format": self.accumulator_spill_format,
            "accumulator_spill_chunk_schema": (
                STREAMING_CHUNK_SCHEMA if self.streaming_spill else self.chunk_schema_version
            ),
            "max_unique_fingerprints": self.max_unique_fingerprints,
            "candidates_seen": self.candidates_seen,
            "hot_path_exact_fingerprint_duplicates": self.hot_path_exact_fingerprint_duplicates,
            "hot_path_better_duplicate_replacements": self.hot_path_better_duplicate_replacements,
            "spill_chunks": list(self.spill_chunks),
            "spilled_candidates": self.spilled_candidate_count,
            "spilled_unique_fingerprints": self.spilled_unique_fingerprint_count,
            "spill_bytes": self.spilled_bytes,
            "plan_sha256": self.plan_sha256,
            "stage_contract_sha256": self.stage_contract_sha256,
            "streaming_spill": self.streaming_spill,
            "peak_spill_serialization_buffer_bytes": self.peak_spill_serialization_buffer_bytes,
            "peak_spill_restore_buffer_bytes": self.peak_spill_restore_buffer_bytes,
            "peak_spill_chunk_uncompressed_bytes": self.peak_spill_chunk_uncompressed_bytes,
            "peak_finalization_unique_node_count": self.peak_finalization_unique_node_count,
            "peak_finalization_unique_set_bytes": self.peak_finalization_unique_set_bytes,
            "peak_final_sort_node_count": self.peak_final_sort_node_count,
            "peak_final_sort_list_bytes": self.peak_final_sort_list_bytes,
            "finalization_needed": self.finalization_needed,
            **self._timing_metrics(),
            "nodes": [node.to_json() for node in sorted(self.best_by_fingerprint.values(), key=_node_order_key)],
        }

    @classmethod
    def from_json(
        cls,
        payload: dict[str, Any],
        *,
        stage: dict[str, Any],
        spill_root: Path | None = None,
        output_root: Path | None = None,
        plan_sha256: str = "unbound_test_plan",
        stage_contract_sha256: str | None = None,
    ) -> "DestinationBucketAccumulator":
        if payload.get("schema_version") != cls.schema_version:
            raise ValueError(f"Unsupported destination accumulator schema: {payload.get('schema_version')!r}")
        accumulator = cls(
            bucket_index=int(payload["bucket_index"]),
            stage=stage,
            max_unique_fingerprints=int(payload.get("max_unique_fingerprints", _accumulator_unique_bound(stage))),
            spill_root=spill_root,
            output_root=output_root,
            plan_sha256=plan_sha256,
            stage_contract_sha256=stage_contract_sha256,
        )
        declared_spill_format = payload.get("accumulator_spill_format")
        if declared_spill_format is not None and declared_spill_format != accumulator.accumulator_spill_format:
            raise ValueError(
                "Destination accumulator spill-format mismatch: "
                f"{declared_spill_format!r} != {accumulator.accumulator_spill_format!r}"
            )
        accumulator.candidates_seen = int(payload.get("candidates_seen", 0))
        accumulator.hot_path_exact_fingerprint_duplicates = int(payload.get("hot_path_exact_fingerprint_duplicates", payload.get("exact_fingerprint_duplicates", 0)))
        accumulator.hot_path_better_duplicate_replacements = int(payload.get("hot_path_better_duplicate_replacements", payload.get("better_duplicate_replacements", 0)))
        accumulator.spill_chunks = list(payload.get("spill_chunks", []))
        accumulator.spilled_candidate_count = int(payload.get("spilled_candidates", 0))
        accumulator.spilled_unique_fingerprint_count = int(payload.get("spilled_unique_fingerprints", 0))
        accumulator.spilled_bytes = int(payload.get("spill_bytes", 0))
        accumulator.retained_set_finalization_count = int(payload.get("retained_set_finalization_count", 0))
        accumulator.full_retained_set_scan_count = int(payload.get("full_retained_set_scan_count", 0))
        accumulator.peak_spill_serialization_buffer_bytes = int(payload.get("peak_spill_serialization_buffer_bytes", 0))
        accumulator.peak_spill_restore_buffer_bytes = int(payload.get("peak_spill_restore_buffer_bytes", 0))
        accumulator.peak_spill_chunk_uncompressed_bytes = int(payload.get("peak_spill_chunk_uncompressed_bytes", 0))
        accumulator.peak_finalization_unique_node_count = int(payload.get("peak_finalization_unique_node_count", 0))
        accumulator.peak_finalization_unique_set_bytes = int(payload.get("peak_finalization_unique_set_bytes", 0))
        accumulator.peak_final_sort_node_count = int(payload.get("peak_final_sort_node_count", 0))
        accumulator.peak_final_sort_list_bytes = int(payload.get("peak_final_sort_list_bytes", 0))
        accumulator.spill_write_count = int(payload.get("spill_write_count", 0))
        accumulator.spill_write_seconds = float(payload.get("spill_write_seconds", 0.0))
        accumulator.spill_sha_validation_count = int(payload.get("spill_sha_validation_count", 0))
        accumulator.spill_sha_validation_seconds = float(payload.get("spill_sha_validation_seconds", 0.0))
        accumulator.spill_restore_pass_count = int(payload.get("spill_restore_pass_count", 0))
        accumulator.spill_restore_nodes_streamed = int(payload.get("spill_restore_nodes_streamed", 0))
        accumulator.spill_restore_seconds = float(payload.get("spill_restore_seconds", 0.0))
        accumulator.full_accumulator_finalization_count = int(payload.get("full_accumulator_finalization_count", payload.get("full_retained_set_scan_count", 0)))
        accumulator.accumulator_finalization_seconds = float(payload.get("accumulator_finalization_seconds", 0.0))
        accumulator.duplicate_merge_seconds = float(payload.get("duplicate_merge_seconds", 0.0))
        accumulator.retained_selection_seconds = float(payload.get("retained_selection_seconds", 0.0))
        accumulator.finalization_needed = bool(payload.get("finalization_needed", True))
        for item in payload.get("nodes", []):
            node = BeamNode.from_json(item)
            accumulator.best_by_fingerprint[node.future_fingerprint] = node
        minimum_seen = len(accumulator.best_by_fingerprint) + sum(int(chunk.get("candidate_count", 0)) for chunk in accumulator.spill_chunks)
        if accumulator.candidates_seen < minimum_seen:
            accumulator.candidates_seen = minimum_seen
        return accumulator


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Candidate 111 deterministic diverse time-bucket Beam Search.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--dry-run-plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--only-stage", type=str, default=None)
    parser.add_argument("--max-expansions", type=int, default=None)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--smoke-run", action="store_true")
    parser.add_argument("--wall-clock-limit-seconds", type=float, default=None)
    parser.add_argument("--memory-budget-bytes", type=int, default=None)
    return parser


def parse_and_validate_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not args.dry_run_plan and not args.execute:
        parser.error("No mode selected; use --dry-run-plan or --execute.")
    if args.resume and not args.execute:
        parser.error("--resume requires --execute.")
    if args.max_expansions is not None and args.max_expansions <= 0:
        parser.error("--max-expansions must be positive.")
    if args.wall_clock_limit_seconds is not None and args.wall_clock_limit_seconds <= 0:
        parser.error("--wall-clock-limit-seconds must be positive.")
    if args.memory_budget_bytes is not None and args.memory_budget_bytes <= 0:
        parser.error("--memory-budget-bytes must be positive.")
    if args.smoke_run and args.output_root is not None:
        output = args.output_root.resolve()
        if output == CANONICAL_RESULTS_ROOT.resolve() or CANONICAL_RESULTS_ROOT.resolve() in output.parents:
            parser.error("--smoke-run cannot target canonical results/beam_search_v111 output.")
    return args


def dry_run_plan(plan_path: Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    validation = validate_plan(plan, plan_path=plan_path)
    memory_estimates = {stage["stage_id"]: _memory_estimate_for_stage(plan, stage) for stage in plan["stages"]}
    return {
        "status": "beam_search_dry_run_plan_ok",
        "plan": validation,
        "future_configuration": {
            "algorithm": plan["algorithm"],
            "objective": plan["objective"],
            "party": plan["party"],
            "initial_active_character": plan["initial_active_character"],
            "curriculum_reset_mode": plan["curriculum_reset_mode"],
            "route_similarity_objective": plan["route_similarity_objective"],
            "manual_route_guidance": plan["manual_route_guidance"],
            "bc_ppo_policy_guidance": plan["bc_ppo_policy_guidance"],
            "stages": plan["stages"],
            "termination_statuses": sorted(TERMINATION_STATUSES),
            "memory_estimates": memory_estimates,
        },
        "actual_data_hashes": validation["actual_data_hashes"],
        "canonical_output_created": _canonical_output_root(plan, plan_path).exists(),
    }


def run_search_from_args(args: argparse.Namespace) -> dict[str, Any]:
    plan = load_plan(args.plan)
    validate_plan(plan, plan_path=args.plan)
    if args.dry_run_plan:
        return dry_run_plan(args.plan)
    if args.smoke_run:
        stage = _smoke_stage(args.max_expansions)
    else:
        stage_id = args.only_stage or str(plan["stages"][0]["stage_id"])
        stage = dict(stage_by_id(plan, stage_id))
        if args.max_expansions is not None:
            stage["maximum_expansions"] = min(stage["maximum_expansions"], args.max_expansions)
    if args.wall_clock_limit_seconds is not None:
        stage["wall_clock_limit_seconds"] = float(args.wall_clock_limit_seconds)
    if args.memory_budget_bytes is not None:
        configured_budget = stage.get("memory_budget_bytes")
        if configured_budget is not None and int(args.memory_budget_bytes) > int(configured_budget):
            raise ValueError("--memory-budget-bytes may lower, but may not raise, the reviewed stage budget")
        stage["memory_budget_bytes"] = int(args.memory_budget_bytes)
    lowmem_plan = is_low_memory_execution_plan(plan)
    if lowmem_plan and stage.get("memory_budget_bytes") is None:
        raise ValueError("The 32 GB Beam stage requires a hard memory budget")
    canonical_output_root = _canonical_output_root(plan, args.plan)
    output_root = args.output_root or canonical_output_root
    resolved_output = output_root.resolve()
    forbidden_roots = [
        (ROOT / str(relative)).resolve()
        for relative in plan.get("output_contract", {}).get("forbidden_resume_or_output_roots", [])
    ]
    if lowmem_plan and any(
        resolved_output == forbidden_output or forbidden_output in resolved_output.parents
        for forbidden_output in forbidden_roots
    ):
        raise ValueError("Low-memory plan refuses output or resume under a forbidden legacy Beam root")
    if (
        args.resume
        and plan.get("resume_extension_contract", {}).get("enabled") is True
        and plan.get("execution_contract", {}).get("canonical_output_root_required_for_resume") is True
        and resolved_output != canonical_output_root.resolve()
    ):
        raise ValueError("Hash-pinned extension resume requires the exact canonical output root")
    if args.smoke_run and output_root.resolve() == canonical_output_root.resolve():
        raise ValueError("--smoke-run requires a temporary/noncanonical output root")
    runner = BeamSearchRunner(plan=plan, stage=stage, plan_path=args.plan, output_root=output_root)
    return runner.run(resume=args.resume)


def compact_cli_summary(result: dict[str, Any]) -> dict[str, Any]:
    output_root = Path(result["output_root"])
    best_completed = result.get("best_completed_search_route") or {}
    best_partial = result.get("best_partial_frontier_node") or {}
    return {
        "schema_version": "beam_search_compact_cli_summary_v111",
        "status": result["status"],
        "termination_status": result["termination_status"],
        "stage_id": result["stage_id"],
        "candidate": result["candidate"],
        "expansions": result["expansions"],
        "elapsed_seconds": result["elapsed_seconds"],
        "expansions_per_second": result["expansions_per_second"],
        "invocation_start_expansions": result["invocation_start_expansions"],
        "invocation_expansions": result["invocation_expansions"],
        "invocation_elapsed_seconds": result["invocation_elapsed_seconds"],
        "invocation_expansions_per_second": result["invocation_expansions_per_second"],
        "cumulative_elapsed_seconds": result["cumulative_elapsed_seconds"],
        "cumulative_expansions_per_second": result["cumulative_expansions_per_second"],
        "output_root": output_root.as_posix(),
        "search_state_path": (output_root / "search_state.json").as_posix(),
        "execution_result_path": (output_root / "execution_result.json").as_posix(),
        "leaderboard_path": (output_root / "leaderboard.json").as_posix(),
        "best_route_path": (output_root / "best_route.json").as_posix(),
        "final_summary_path": (output_root / "final_summary.json").as_posix(),
        "best_completed_total_damage": best_completed.get("total_damage"),
        "best_partial_total_damage": best_partial.get("total_damage"),
        "checkpoint_count": result.get("checkpoint_count"),
        "accumulator_finalization_count": result.get("accumulator_finalization_count"),
        "peak_process_rss_bytes": result.get("peak_process_rss_bytes"),
        "compact_output": True,
    }


class BeamSearchRunner:
    def __init__(self, *, plan: dict[str, Any], stage: dict[str, Any], plan_path: Path, output_root: Path) -> None:
        self.plan = plan
        self.stage = dict(stage)
        self.plan_path = plan_path
        self.plan_sha256 = sha256_file(plan_path)
        self.stage_contract_sha256 = _spill_stage_contract_sha256(stage)
        self.output_root = output_root
        self.frontier_root = output_root / "frontier"
        self.accumulator_root = self.frontier_root / "accumulators"
        self.logs_root = output_root / "logs"
        self.stage_id = stage["stage_id"]
        self.maximum_expansions = int(stage["maximum_expansions"])
        self.time_bucket_width = float(stage["time_bucket_width"])
        self.checkpoint_interval_expansions = int(stage.get("checkpoint_interval_expansions", plan.get("checkpoint_interval_expansions", 100000)))
        self.limit_check_interval_expansions = int(stage.get("limit_check_interval_expansions", plan.get("memory_estimate_contract", {}).get("limit_check_interval_expansions", 64)))
        self.next_checkpoint_expansion = self.checkpoint_interval_expansions
        self.next_node_id = 1
        self.expansions = 0
        self.deduplicated_states = 0
        self.pruned_states = 0
        self.zero_time_expansion_count = 0
        self.completed: list[dict[str, Any]] = []
        self.next_completion_order = 1
        self.completed_buckets: set[int] = set()
        self.route_store: dict[int, dict[str, Any]] = {}
        self.pending: dict[int, list[BeamNode]] = {}
        self.pending_accumulators: dict[int, DestinationBucketAccumulator] = {}
        self.partial_action_cursors: dict[int, int] = {}
        self.bucket_resume_queues: dict[int, list[int]] = {}
        self.dirty_buckets: set[int] = set()
        self.pending_bucket_hashes: dict[int, dict[str, str]] = {}
        self.best_completed_search_route: dict[str, Any] | None = None
        self.completed_leaderboard_size = int(plan.get("completed_route_leaderboard_size", 128))
        self.live_node_count = 0
        self.peak_live_nodes = 0
        self.peak_frontier_size = 0
        self.peak_serialized_payload_bytes = 0
        self.peak_process_rss_bytes = _process_peak_rss_bytes()
        self.checkpoint_count = 0
        self.frontier_file_write_count = 0
        self.metric_update_count = 0
        self.payload_size_calculation_count = 0
        self.bucket_metrics: list[dict[str, Any]] = []
        self.accumulator_finalization_count = 0
        self.retired_accumulator_lifecycle_metrics = {key: 0 for key in ACCUMULATOR_LIFECYCLE_METRIC_KEYS}
        self.phase_timing_metrics: dict[str, float | int] = {
            "checkpoint_manifest_generation_count": 0,
            "forced_checkpoint_manifest_generation_count": 0,
            "checkpoint_manifest_generation_seconds": 0.0,
            "pending_frontier_serialization_count": 0,
            "pending_frontier_serialization_seconds": 0.0,
            "route_store_compaction_count": 0,
            "route_store_compaction_seconds": 0.0,
            "result_creation_count": 0,
            "result_creation_seconds": 0.0,
        }
        self.invocation_started_at: float | None = None
        self.invocation_start_expansions = 0
        self.prior_cumulative_elapsed_seconds = 0.0
        self.cumulative_accounting_complete = True

    def run(self, *, resume: bool = False) -> dict[str, Any]:
        started = time.perf_counter()
        self.invocation_started_at = started
        if self.output_root.exists() and not resume and any(self.output_root.iterdir()):
            raise ValueError(f"Non-resume Beam Search cannot target non-empty output root: {self.output_root}")
        resume_context = self._resolve_resume_context() if resume else None
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.frontier_root.mkdir(parents=True, exist_ok=True)
        self.accumulator_root.mkdir(parents=True, exist_ok=True)
        self.logs_root.mkdir(parents=True, exist_ok=True)
        self._write_log(f"stage {self.stage_id} start resume={resume}")
        template = self._create_simulation()
        if resume:
            self._load_resume_state(resume_context)
        else:
            self.invocation_start_expansions = 0
            root_node = make_node(simulation=template, node_id=0)
            self.route_store[root_node.node_id] = _route_edge(root_node)
            root_bucket = self._bucket(root_node.combat_time)
            root_accumulator = self._new_accumulator(root_bucket)
            root_accumulator.add(root_node)
            self.pending_accumulators[root_bucket] = root_accumulator
            self.pending = {root_bucket: self._finalize_accumulator_view(root_bucket, root_accumulator)}
            self.live_node_count = 1
            self._mark_bucket_dirty(root_bucket)
            self._update_peak_metrics(root_node)
            self._save_manifest(status="interrupted_resumable", force=True)
        termination_status = "frontier_exhausted_without_complete_route"
        while self.pending:
            if self.expansions >= self.maximum_expansions:
                termination_status = "expansion_budget_exhausted"
                break
            if self._wall_clock_exceeded(started):
                termination_status = "wall_clock_budget_exhausted"
                break
            if self._memory_budget_exceeded():
                termination_status = "memory_budget_exhausted"
                break
            bucket_index = min(self.pending)
            nodes = self.pending.pop(bucket_index)
            self.live_node_count -= len(nodes)
            resume_queue = self.bucket_resume_queues.pop(bucket_index, [])
            accumulator = self.pending_accumulators.get(bucket_index)
            retire_accumulator = accumulator is not None and not resume_queue
            if not resume_queue:
                accumulator = self.pending_accumulators.pop(bucket_index, None)
            before_count = len(nodes) if accumulator is None else accumulator.candidates_seen
            if resume_queue:
                by_id = {node.node_id: node for node in nodes}
                retained = [by_id[node_id] for node_id in resume_queue if node_id in by_id]
                retained_ids = {node.node_id for node in retained}
                deferred = [node for node in nodes if node.node_id not in retained_ids]
                if deferred:
                    self._prepend_pending(bucket_index, deferred)
            else:
                if accumulator is None:
                    retained = self._retain(nodes)
                else:
                    finalized = self._finalize_accumulator(bucket_index, accumulator)
                    retained = finalized["retained"]
                    self._count_finalized_accumulator_metrics(finalized["metrics"])
                    if retire_accumulator:
                        self._retire_accumulator_metrics(accumulator)
            self._compact_route_store(extra_node_ids=[node.node_id for node in retained])
            metric = {
                "bucket_index": bucket_index,
                "input_count": before_count,
                "retained_before_expand": len(retained),
                "expanded_nodes": 0,
                "children": 0,
                "completed_children": 0,
                "deduplicated_total_after_bucket": self.deduplicated_states,
                "pruned_total_after_bucket": self.pruned_states,
            }
            for retained_index, node in enumerate(retained):
                budget_status = self._budget_limit_status(started, force=True)
                if budget_status is not None:
                    self._defer_retained_queue(bucket_index, retained[retained_index:])
                    self._mark_bucket_dirty(bucket_index)
                    termination_status = budget_status
                    break
                if self.expansions >= self.maximum_expansions:
                    self._defer_retained_queue(bucket_index, retained[retained_index:])
                    self._mark_bucket_dirty(bucket_index)
                    termination_status = "expansion_budget_exhausted"
                    break
                simulation = restore_simulation_from_state(template, node.state_payload)
                if simulation.state.combat_time >= simulation.combat_duration:
                    self._record_completed(node)
                    metric["completed_children"] += 1
                    continue
                valid_actions = list(simulation.valid_action_ids())
                start_action_index = self.partial_action_cursors.pop(node.node_id, 0)
                for action_index, action_id in enumerate(valid_actions[start_action_index:], start=start_action_index):
                    if self.expansions >= self.maximum_expansions:
                        self._defer_retained_queue(bucket_index, retained[retained_index:])
                        self.partial_action_cursors[node.node_id] = action_index
                        self._mark_bucket_dirty(bucket_index)
                        termination_status = "expansion_budget_exhausted"
                        break
                    child_sim = clone_simulation_for_search(simulation)
                    before_combat = child_sim.state.combat_time
                    before_fingerprint = node.future_fingerprint
                    if not child_sim.execute_action(action_id):
                        raise RuntimeError(f"Action reported available but failed execution: {action_id}")
                    if child_sim.state.combat_time + 1e-12 < before_combat:
                        raise RuntimeError("Beam child combat time regressed")
                    if abs(child_sim.state.combat_time - before_combat) <= 1e-12:
                        self.zero_time_expansion_count += 1
                    resolved = child_sim.timeline[-1].resolved_action_id if child_sim.timeline else child_sim.resolve_action_id(action_id)
                    child = make_node(
                        simulation=child_sim,
                        node_id=self.next_node_id,
                        parent=node,
                        selected_action_id=action_id,
                        resolved_action_id=resolved,
                    )
                    self.next_node_id += 1
                    self.expansions += 1
                    self.payload_size_calculation_count += 1
                    metric["children"] += 1
                    if (
                        child.future_fingerprint == before_fingerprint
                        and child.total_damage <= node.total_damage
                        and abs(child.combat_time - node.combat_time) <= 1e-12
                    ):
                        self.pruned_states += 1
                        continue
                    self.route_store[child.node_id] = _route_edge(child)
                    child_bucket = self._bucket(child.combat_time)
                    if child.complete:
                        self._finalize_route_hashes(child)
                        self._record_completed(child)
                        metric["completed_children"] += 1
                    else:
                        self._add_pending_node(child_bucket, child)
                    self._update_peak_metrics(child)
                    budget_status = self._budget_limit_status(started)
                    if budget_status is not None:
                        self._interrupt_retained_queue(
                            bucket_index=bucket_index,
                            retained=retained,
                            retained_index=retained_index,
                            node_id=node.node_id,
                            next_action_index=action_index + 1,
                            action_count=len(valid_actions),
                        )
                        self._mark_bucket_dirty(bucket_index)
                        termination_status = budget_status
                        break
                metric["expanded_nodes"] += 1
                if termination_status in {"expansion_budget_exhausted", "wall_clock_budget_exhausted", "memory_budget_exhausted"}:
                    break
            if not self.pending.get(bucket_index):
                self.completed_buckets.add(bucket_index)
            self.bucket_metrics.append(metric)
            self._compact_route_store()
            if self._checkpoint_due() and termination_status not in {"expansion_budget_exhausted", "wall_clock_budget_exhausted", "memory_budget_exhausted"}:
                self._save_manifest(status="interrupted_resumable")
            if termination_status in {"expansion_budget_exhausted", "wall_clock_budget_exhausted", "memory_budget_exhausted"}:
                break
        else:
            termination_status = "completed_search" if self.completed else "frontier_exhausted_without_complete_route"
        elapsed = time.perf_counter() - started
        result_started = time.perf_counter()
        result = self._result_payload(status=termination_status, elapsed=elapsed)
        self.phase_timing_metrics["result_creation_count"] = int(self.phase_timing_metrics["result_creation_count"]) + 1
        self.phase_timing_metrics["result_creation_seconds"] = float(self.phase_timing_metrics["result_creation_seconds"]) + (time.perf_counter() - result_started)
        result["phase_timing_metrics"] = dict(self.phase_timing_metrics)
        self._atomic_json(self.output_root / "execution_result.json", result)
        incumbent = load_project_comparison_incumbent(self.plan) if self.stage.get("result_scope") == "completed_120s_project_comparison" else None
        self._atomic_json(self.output_root / "leaderboard.json", _leaderboard_payload(result, self.stage_id, result_scope=self.stage.get("result_scope"), incumbent=incumbent))
        self._atomic_json(self.output_root / "best_route.json", _best_route_payload(result, self.stage_id, result_scope=self.stage.get("result_scope"), incumbent=incumbent))
        self._atomic_json(self.output_root / "final_summary.json", _summary_payload(result, self.stage_id, result_scope=self.stage.get("result_scope"), incumbent=incumbent))
        self._write_log(f"stage {self.stage_id} complete status={termination_status} expansions={self.expansions}")
        return result

    def _create_simulation(self) -> Simulation:
        simulation = Simulation.from_json(
            ROOT / "data",
            selected_character_ids=self.plan["party"],
            initial_active_character=self.plan["initial_active_character"],
            transition_config=None,
        )
        simulation.combat_duration = float(self.stage["combat_duration"])
        simulation.state.combat_duration = simulation.combat_duration
        return simulation

    def _retain(self, nodes: list[BeamNode]) -> list[BeamNode]:
        result = _select_retained_batch(nodes, self.stage)
        self.deduplicated_states += int(result["metrics"]["exact_fingerprint_duplicates"])
        self.pruned_states += int(result["metrics"]["final_rejected_count"])
        return result["retained"]

    def _finalize_accumulator_view(self, bucket_index: int, accumulator: DestinationBucketAccumulator) -> list[BeamNode]:
        return self._finalize_accumulator(bucket_index, accumulator)["retained"]

    def _finalize_accumulator(self, bucket_index: int, accumulator: DestinationBucketAccumulator) -> dict[str, Any]:
        _ = bucket_index
        before = accumulator.full_accumulator_finalization_count
        finalized = accumulator.finalize_retention()
        self.accumulator_finalization_count += accumulator.full_accumulator_finalization_count - before
        return finalized

    def _count_finalized_accumulator_metrics(self, metrics: dict[str, Any]) -> None:
        self.deduplicated_states += int(metrics["exact_fingerprint_duplicates"])
        self.pruned_states += int(metrics["final_rejected_count"])

    def _record_completed(self, node: BeamNode) -> None:
        self._finalize_route_hashes(node)
        record = self._completed_record(node, completion_order=self.next_completion_order)
        self.next_completion_order += 1
        self.completed.append(record)
        self.completed = sorted(self.completed, key=lambda item: (-float(item["total_damage"]), int(item["completion_order"])))[: self.completed_leaderboard_size]
        if self.best_completed_search_route is None or (
            float(record["total_damage"]),
            -int(record["completion_order"]),
        ) > (
            float(self.best_completed_search_route["total_damage"]),
            -int(self.best_completed_search_route["completion_order"]),
        ):
            self.best_completed_search_route = record

    def _finalize_route_hashes(self, node: BeamNode) -> None:
        selected, resolved = self.reconstruct_route(node.node_id)
        node.selected_sequence_sha256 = sequence_sha256(selected)
        node.resolved_sequence_sha256 = sequence_sha256(resolved)
        node.route_id = node.selected_sequence_sha256[:16]

    def reconstruct_route(self, node_id: int) -> tuple[list[str], list[str]]:
        selected: list[str] = []
        resolved: list[str] = []
        current: int | None = node_id
        while current is not None:
            edge = self.route_store[current]
            if edge.get("selected_action_id") is not None:
                selected.append(edge["selected_action_id"])
            if edge.get("resolved_action_id") is not None:
                resolved.append(edge["resolved_action_id"])
            current = edge.get("parent_id")
        selected.reverse()
        resolved.reverse()
        return selected, resolved

    def _completed_record(self, node: BeamNode, *, completion_order: int) -> dict[str, Any]:
        selected, resolved = self.reconstruct_route(node.node_id)
        return {
            "schema_version": "beam_search_completed_route_v111",
            "terminal_node_id": node.node_id,
            "route_id": node.route_id,
            "completion_order": completion_order,
            "total_damage": node.total_damage,
            "dps": node.total_damage / max(float(self.stage["combat_duration"]), 1e-9),
            "combat_time": node.combat_time,
            "current_time": node.current_time,
            "action_count": node.action_count,
            "selected_sequence_sha256": node.selected_sequence_sha256,
            "resolved_sequence_sha256": node.resolved_sequence_sha256,
            "selected_sequence": selected,
            "resolved_sequence": resolved,
        }

    def _bucket(self, combat_time: float) -> int:
        return int(float(combat_time) / self.time_bucket_width)

    def _save_manifest(self, *, status: str, force: bool = False) -> None:
        checkpoint_started = time.perf_counter()
        self.phase_timing_metrics["checkpoint_manifest_generation_count"] = int(self.phase_timing_metrics["checkpoint_manifest_generation_count"]) + 1
        if force:
            self.phase_timing_metrics["forced_checkpoint_manifest_generation_count"] = int(self.phase_timing_metrics["forced_checkpoint_manifest_generation_count"]) + 1
        accumulator_entries: dict[str, dict[str, Any]] = {}
        accumulator_metrics: dict[str, dict[str, Any]] = {}
        for bucket_index, accumulator in sorted(self.pending_accumulators.items()):
            accumulator.spill_current_chunk()
            retained_view_count = len(self.pending.get(bucket_index, []))
            accumulator_entries[str(bucket_index)] = accumulator.manifest(retained_view_count=retained_view_count)
            accumulator_metrics[str(bucket_index)] = accumulator.cheap_metrics()
        pending_entries: list[dict[str, Any]] = []
        wrote_frontier = False
        for bucket_index, nodes in sorted(self.pending.items()):
            rel = self._frontier_rel_path(bucket_index)
            path = self.output_root / rel if not rel.is_absolute() else rel
            existing = self.pending_bucket_hashes.get(bucket_index)
            if force or bucket_index in self.dirty_buckets or existing is None:
                frontier_started = time.perf_counter()
                sha = write_json_gz(path, {"schema_version": "beam_search_frontier_v111", "bucket_index": bucket_index, "nodes": [node.to_json() for node in nodes]})
                self.phase_timing_metrics["pending_frontier_serialization_count"] = int(self.phase_timing_metrics["pending_frontier_serialization_count"]) + 1
                self.phase_timing_metrics["pending_frontier_serialization_seconds"] = float(self.phase_timing_metrics["pending_frontier_serialization_seconds"]) + (time.perf_counter() - frontier_started)
                wrote_frontier = True
                self.frontier_file_write_count += 1
                self.pending_bucket_hashes[bucket_index] = {"path": _path_text(path), "sha256": sha}
            else:
                sha = existing["sha256"]
            entry = {
                "bucket_index": bucket_index,
                "path": _path_text(path),
                "sha256": sha,
                "node_count": len(nodes),
                "dirty_written": bool(force or bucket_index in self.dirty_buckets or existing is None),
            }
            pending_entries.append(entry)
        self.dirty_buckets.clear()
        self.pending_bucket_hashes = {
            int(entry["bucket_index"]): {"path": entry["path"], "sha256": entry["sha256"]}
            for entry in pending_entries
        }
        self._update_peak_metrics()
        self.checkpoint_count += 1
        checkpoint_elapsed = (
            time.perf_counter() - self.invocation_started_at
            if self.invocation_started_at is not None
            else 0.0
        )
        checkpoint_performance = performance_accounting(
            cumulative_expansions=self.expansions,
            invocation_start_expansions=self.invocation_start_expansions,
            invocation_elapsed_seconds=checkpoint_elapsed,
            prior_cumulative_elapsed_seconds=self.prior_cumulative_elapsed_seconds,
            cumulative_accounting_complete=self.cumulative_accounting_complete,
        )
        manifest = {
            "schema_version": "beam_search_resume_manifest_v111_corrected",
            "candidate": self.plan["candidate"],
            "stage_id": self.stage_id,
            "plan_path": _project_relative(self.plan_path),
            "plan_sha256": sha256_file(self.plan_path),
            "stage": self.stage,
            "stage_sha256": _json_sha256(self.stage),
            "accumulator_spill_format": resolve_accumulator_spill_format(self.stage),
            "accumulator_spill_chunk_schema": (
                STREAMING_CHUNK_SCHEMA
                if resolve_accumulator_spill_format(self.stage) == STREAMING_ACCUMULATOR_SPILL_FORMAT
                else DestinationBucketAccumulator.chunk_schema_version
            ),
            "actual_data_hashes": resolve_plan_data_hashes(self.plan),
            "expansions": self.expansions,
            **checkpoint_performance,
            "next_node_id": self.next_node_id,
            "next_completion_order": self.next_completion_order,
            "deduplicated_states": self.deduplicated_states,
            "pruned_states": self.pruned_states,
            "zero_time_expansion_count": self.zero_time_expansion_count,
            "partial_action_cursors": {str(key): value for key, value in self.partial_action_cursors.items()},
            "bucket_resume_queues": {str(key): value for key, value in sorted(self.bucket_resume_queues.items())},
            "peak_live_nodes": self.peak_live_nodes,
            "peak_frontier_size": self.peak_frontier_size,
            "peak_serialized_payload_bytes": self.peak_serialized_payload_bytes,
            "peak_process_rss_bytes": self.peak_process_rss_bytes,
            "live_node_count": self.live_node_count,
            "metric_update_count": self.metric_update_count,
            "payload_size_calculation_count": self.payload_size_calculation_count,
            "checkpoint_count": self.checkpoint_count,
            "frontier_file_write_count": self.frontier_file_write_count,
            "accumulator_finalization_count": self.accumulator_finalization_count,
            "retired_accumulator_lifecycle_metrics": dict(self.retired_accumulator_lifecycle_metrics),
            "phase_timing_metrics": dict(self.phase_timing_metrics),
            "checkpoint_interval_expansions": self.checkpoint_interval_expansions,
            "limit_check_interval_expansions": self.limit_check_interval_expansions,
            "next_checkpoint_expansion": self.next_checkpoint_expansion,
            "wrote_frontier_this_checkpoint": wrote_frontier,
            "frontier_bounds": self._frontier_bounds_payload(),
            "destination_bucket_accumulators": accumulator_entries,
            "destination_bucket_accumulator_metrics": accumulator_metrics,
            "pending_buckets": pending_entries,
            "completed_buckets": sorted(self.completed_buckets),
            "completed_routes": self.completed,
            "best_completed_search_route": self.best_completed_search_route,
            "route_store": {str(key): value for key, value in self.route_store.items()},
            "termination_status": status,
            "bucket_metrics": self.bucket_metrics,
            "log_paths": [_path_text(path) for path in sorted(self.logs_root.glob("*.log"))],
        }
        self._atomic_json(self.output_root / "search_state.json", manifest)
        self.phase_timing_metrics["checkpoint_manifest_generation_seconds"] = float(self.phase_timing_metrics["checkpoint_manifest_generation_seconds"]) + (time.perf_counter() - checkpoint_started)

    def _resolve_resume_context(self) -> dict[str, Any]:
        state_path = self.output_root / "search_state.json"
        if not state_path.exists():
            raise ValueError(f"Cannot resume without search_state.json: {state_path}")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("schema_version") not in {"beam_search_resume_manifest_v111_corrected", "beam_search_state_v111_corrected"}:
            raise ValueError(f"Unsupported resume state schema: {state.get('schema_version')}")
        if state["plan_sha256"] == sha256_file(self.plan_path):
            if not _resume_stage_compatible(state["stage"], self.stage):
                raise ValueError("Beam Search resume stage hash mismatch")
            if state["actual_data_hashes"] != resolve_plan_data_hashes(self.plan):
                raise ValueError("Beam Search resume data-contract hash mismatch")
            return {"resume_mode": "exact_same_plan", "state": state}
        if not _resume_extension_plan_compatible(state, self.plan):
            raise ValueError("Beam Search resume plan hash mismatch")
        project_root = _project_root_for_plan(self.plan_path)
        return validate_hash_pinned_extension(
            project_root=project_root,
            plan_path=self.plan_path,
            plan=self.plan,
            stage=self.stage,
            output_root=self.output_root,
            write_receipt=True,
        )

    def _load_resume_state(self, resume_context: dict[str, Any] | None = None) -> None:
        context = resume_context or self._resolve_resume_context()
        state = context["state"]
        self.expansions = int(state["expansions"])
        self.invocation_start_expansions = self.expansions
        (
            self.prior_cumulative_elapsed_seconds,
            self.cumulative_accounting_complete,
        ) = migrate_prior_accounting(state)
        self.next_node_id = int(state["next_node_id"])
        self.next_completion_order = int(state.get("next_completion_order", _next_completion_order_from_records(state.get("completed_routes", []))))
        self.deduplicated_states = int(state["deduplicated_states"])
        self.pruned_states = int(state["pruned_states"])
        self.zero_time_expansion_count = int(state.get("zero_time_expansion_count", 0))
        self.peak_live_nodes = int(state.get("peak_live_nodes", 0))
        self.peak_frontier_size = int(state.get("peak_frontier_size", 0))
        self.peak_serialized_payload_bytes = int(state.get("peak_serialized_payload_bytes", 0))
        self.peak_process_rss_bytes = max(int(state.get("peak_process_rss_bytes", 0)), _process_peak_rss_bytes())
        self.completed_buckets = {int(item) for item in state.get("completed_buckets", [])}
        self.completed = list(state.get("completed_routes", []))
        self.best_completed_search_route = state.get("best_completed_search_route")
        self.route_store = {int(key): value for key, value in state["route_store"].items()}
        self.partial_action_cursors = {int(key): int(value) for key, value in state.get("partial_action_cursors", {}).items()}
        self.bucket_resume_queues = {int(key): [int(item) for item in value] for key, value in state.get("bucket_resume_queues", {}).items()}
        self.live_node_count = int(state.get("live_node_count", 0))
        self.metric_update_count = int(state.get("metric_update_count", 0))
        self.payload_size_calculation_count = int(state.get("payload_size_calculation_count", 0))
        self.checkpoint_count = int(state.get("checkpoint_count", 0))
        self.frontier_file_write_count = int(state.get("frontier_file_write_count", 0))
        self.next_checkpoint_expansion = int(state.get("next_checkpoint_expansion", self.checkpoint_interval_expansions))
        self.bucket_metrics = list(state.get("bucket_metrics", []))
        self.accumulator_finalization_count = int(state.get("accumulator_finalization_count", 0))
        for key, value in state.get("retired_accumulator_lifecycle_metrics", {}).items():
            if key in self.retired_accumulator_lifecycle_metrics:
                self.retired_accumulator_lifecycle_metrics[key] = value
        for key, value in state.get("phase_timing_metrics", {}).items():
            if key in self.phase_timing_metrics:
                self.phase_timing_metrics[key] = value
        self.pending = {}
        for entry in state.get("pending_buckets", []):
            path = _resolve_stored_path(str(entry["path"]), self.output_root)
            payload = read_json_gz(path, entry["sha256"])
            self.pending[int(entry["bucket_index"])] = [BeamNode.from_json(item) for item in payload["nodes"]]
            self.pending_bucket_hashes[int(entry["bucket_index"])] = {"path": entry["path"], "sha256": entry["sha256"]}
        self.pending_accumulators = {}
        for key, payload in state.get("destination_bucket_accumulators", {}).items():
            accumulator = DestinationBucketAccumulator.from_json(
                payload,
                stage=self.stage,
                spill_root=self.accumulator_root,
                output_root=self.output_root,
                plan_sha256=self.plan_sha256,
                stage_contract_sha256=self.stage_contract_sha256,
            )
            bucket_index = int(key)
            self.pending_accumulators[bucket_index] = accumulator
            file_ids = [node.node_id for node in self.pending.get(bucket_index, [])]
            resume_ids = self.bucket_resume_queues.get(bucket_index, [])
            exact_ids = set(accumulator.node_ids()) | set(resume_ids)
            if file_ids and not set(file_ids).issubset(exact_ids):
                raise ValueError(f"Destination accumulator checkpoint view mismatch for bucket {bucket_index}")
            self.pending.setdefault(bucket_index, [])
        actual_live_node_count = sum(len(nodes) for nodes in self.pending.values())
        if actual_live_node_count != self.live_node_count:
            raise ValueError(
                f"Beam Search resume live-node count mismatch: manifest={self.live_node_count} actual={actual_live_node_count}"
            )
        for nodes in self.pending.values():
            for node in nodes:
                self.peak_serialized_payload_bytes = max(self.peak_serialized_payload_bytes, int(node.payload_size_bytes))
        self._update_peak_metrics()
        self._assert_frontier_bounds()
        if not self.pending and not self.completed:
            raise ValueError("Resume state contains no pending or completed routes")

    def _result_payload(self, *, status: str, elapsed: float) -> dict[str, Any]:
        self._compact_route_store()
        self._save_manifest(status=status, force=True)
        # Final reporting must exercise incremental restore/finalization so the
        # packaged low-memory metrics prove the selected spill path was read.
        for bucket_index, accumulator in sorted(self.pending_accumulators.items()):
            self._finalize_accumulator(bucket_index, accumulator)
        best_live = self._best_live_node()
        completed_payloads = list(self.completed)
        route_replay_summaries = []
        if self.best_completed_search_route is not None:
            route_replay_summaries.append(
                self._replay_completed_route(self.best_completed_search_route)
            )
        partial_payload = None if best_live is None else best_live.to_json() | {"selected_sequence": self.reconstruct_route(best_live.node_id)[0], "resolved_sequence": self.reconstruct_route(best_live.node_id)[1]}
        performance = performance_accounting(
            cumulative_expansions=self.expansions,
            invocation_start_expansions=self.invocation_start_expansions,
            invocation_elapsed_seconds=elapsed,
            prior_cumulative_elapsed_seconds=self.prior_cumulative_elapsed_seconds,
            cumulative_accounting_complete=self.cumulative_accounting_complete,
        )
        payload = {
            "schema_version": "beam_search_state_v111_corrected",
            "status": status,
            "termination_status": status,
            "stage_id": self.stage_id,
            "candidate": self.plan["candidate"],
            "output_root": self.output_root.resolve().as_posix(),
            "plan_path": _project_relative(self.plan_path),
            "plan_sha256": sha256_file(self.plan_path),
            "stage": self.stage,
            "stage_sha256": _json_sha256(self.stage),
            "accumulator_spill_format": resolve_accumulator_spill_format(self.stage),
            "accumulator_spill_chunk_schema": (
                STREAMING_CHUNK_SCHEMA
                if resolve_accumulator_spill_format(self.stage) == STREAMING_ACCUMULATOR_SPILL_FORMAT
                else DestinationBucketAccumulator.chunk_schema_version
            ),
            "actual_data_hashes": resolve_plan_data_hashes(self.plan),
            "expansions": self.expansions,
            "next_node_id": self.next_node_id,
            "next_completion_order": self.next_completion_order,
            "maximum_expansions": self.maximum_expansions,
            "deduplicated_states": self.deduplicated_states,
            "pruned_states": self.pruned_states,
            "completed_route_count": len(self.completed),
            "zero_time_expansion_count": self.zero_time_expansion_count,
            "partial_action_cursors": {str(key): value for key, value in self.partial_action_cursors.items()},
            "bucket_resume_queues": {str(key): value for key, value in sorted(self.bucket_resume_queues.items())},
            "live_node_count": self.live_node_count,
            "next_checkpoint_expansion": self.next_checkpoint_expansion,
            "peak_frontier_size": self.peak_frontier_size,
            "peak_live_nodes": self.peak_live_nodes,
            "peak_serialized_payload_bytes": self.peak_serialized_payload_bytes,
            "peak_process_rss_bytes": self.peak_process_rss_bytes,
            "estimated_peak_memory_bytes": self._tracked_memory_estimate()["conservative_total_bytes"],
            "tracked_memory_estimate": self._tracked_memory_estimate(),
            **performance,
            "checkpoint_count": self.checkpoint_count,
            "frontier_file_write_count": self.frontier_file_write_count,
            "accumulator_finalization_count": self.accumulator_finalization_count,
            "accumulator_lifecycle_metrics": self._accumulator_lifecycle_metrics(),
            "phase_timing_metrics": dict(self.phase_timing_metrics),
            "metric_update_count": self.metric_update_count,
            "payload_size_calculation_count": self.payload_size_calculation_count,
            "checkpoint_interval_expansions": self.checkpoint_interval_expansions,
            "limit_check_interval_expansions": self.limit_check_interval_expansions,
            "frontier_bounds": self._frontier_bounds_payload(),
            "destination_bucket_accumulator_metrics": {
                str(bucket_index): accumulator.cheap_metrics()
                for bucket_index, accumulator in sorted(self.pending_accumulators.items())
            },
            "destination_bucket_accumulators": {
                str(bucket_index): accumulator.manifest(retained_view_count=len(self.pending.get(bucket_index, [])))
                for bucket_index, accumulator in sorted(self.pending_accumulators.items())
            },
            "bucket_metrics": self.bucket_metrics,
            "completed_routes": completed_payloads,
            "best_completed_search_route": self.best_completed_search_route,
            "route_replay_summaries": route_replay_summaries,
            "historical_verified_bc_reference": verified_bc_incumbent_manifest(),
            "best_partial_frontier_node": partial_payload,
            "pending_buckets": [
                {
                    "bucket_index": bucket_index,
                    "path": data["path"],
                    "sha256": data["sha256"],
                    "node_count": len(self.pending.get(bucket_index, [])),
                }
                for bucket_index, data in sorted(self.pending_bucket_hashes.items())
            ],
            "pending_bucket_indices": sorted(self.pending),
            "completed_buckets": sorted(self.completed_buckets),
            "route_store": {str(key): value for key, value in self.route_store.items()},
            "route_store_entry_count": len(self.route_store),
            "canonical_path_policy": "project_relative_posix",
        }
        if self.stage.get("result_scope") == "completed_120s_project_comparison":
            payload["project_comparison_incumbent"] = load_project_comparison_incumbent(self.plan)
            payload["partial_nodes_excluded_from_final_winner"] = True
        return payload

    def _best_live_node(self) -> BeamNode | None:
        live = [node for nodes in self.pending.values() for node in nodes]
        if not live:
            return None
        return sorted(live, key=_node_order_key)[0]

    def _retire_accumulator_metrics(self, accumulator: DestinationBucketAccumulator) -> None:
        snapshot = accumulator.cheap_metrics()
        for key in ACCUMULATOR_LIFECYCLE_METRIC_KEYS:
            self.retired_accumulator_lifecycle_metrics[key] += snapshot.get(key, 0)

    def _accumulator_lifecycle_metrics(self) -> dict[str, float | int]:
        totals = dict(self.retired_accumulator_lifecycle_metrics)
        for accumulator in self.pending_accumulators.values():
            snapshot = accumulator.cheap_metrics()
            for key in ACCUMULATOR_LIFECYCLE_METRIC_KEYS:
                totals[key] += snapshot.get(key, 0)
        return totals

    def _replay_completed_route(self, route: dict[str, Any]) -> dict[str, Any]:
        summary = replay_selected_route_to_files(
            selected_sequence=list(route["selected_sequence"]),
            output_root=self.output_root,
            route_id=str(route["route_id"]),
            combat_duration=float(self.stage["combat_duration"]),
            party=self.plan["party"],
            initial_active_character=self.plan["initial_active_character"],
            terminal_record=route,
        )
        return summary

    def _mark_bucket_dirty(self, bucket_index: int) -> None:
        self.dirty_buckets.add(int(bucket_index))

    def _prepend_pending(self, bucket_index: int, nodes: list[BeamNode]) -> None:
        if not nodes:
            return
        existing = self.pending.get(bucket_index, [])
        self.pending[bucket_index] = list(nodes) + existing
        self.live_node_count += len(nodes)
        for node in nodes:
            self.peak_serialized_payload_bytes = max(self.peak_serialized_payload_bytes, int(node.payload_size_bytes))
        self._update_peak_metrics()
        self._mark_bucket_dirty(bucket_index)
        self._assert_frontier_bounds()

    def _defer_retained_queue(self, bucket_index: int, nodes: list[BeamNode]) -> None:
        if not nodes:
            return
        self._prepend_pending(bucket_index, nodes)
        existing = self.bucket_resume_queues.get(bucket_index, [])
        self.bucket_resume_queues[bucket_index] = [node.node_id for node in nodes] + existing

    def _interrupt_retained_queue(
        self,
        *,
        bucket_index: int,
        retained: list[BeamNode],
        retained_index: int,
        node_id: int,
        next_action_index: int,
        action_count: int,
    ) -> None:
        if next_action_index < action_count:
            self.partial_action_cursors[node_id] = next_action_index
            self._defer_retained_queue(bucket_index, retained[retained_index:])
        else:
            self.partial_action_cursors.pop(node_id, None)
            self._defer_retained_queue(bucket_index, retained[retained_index + 1 :])

    def _add_pending_node(self, bucket_index: int, node: BeamNode) -> None:
        existing = self.pending.get(bucket_index, [])
        accumulator = self.pending_accumulators.get(bucket_index)
        if accumulator is None:
            accumulator = self._new_accumulator(bucket_index)
            for existing_node in existing:
                accumulator.add(existing_node)
            self.pending_accumulators[bucket_index] = accumulator
        add_result = accumulator.add(node)
        _ = add_result
        if bucket_index not in self.pending:
            self.pending[bucket_index] = existing
        self._mark_bucket_dirty(bucket_index)
        self._update_peak_metrics(node)
        self._assert_frontier_bounds()

    def _new_accumulator(self, bucket_index: int) -> DestinationBucketAccumulator:
        return DestinationBucketAccumulator(
            bucket_index=bucket_index,
            stage=self.stage,
            max_unique_fingerprints=_accumulator_in_memory_limit(self.stage),
            spill_root=self.accumulator_root,
            output_root=self.output_root,
            plan_sha256=self.plan_sha256,
            stage_contract_sha256=self.stage_contract_sha256,
        )

    def _checkpoint_due(self) -> bool:
        if self.checkpoint_interval_expansions <= 0:
            return False
        if self.expansions < self.next_checkpoint_expansion:
            return False
        while self.next_checkpoint_expansion <= self.expansions:
            self.next_checkpoint_expansion += self.checkpoint_interval_expansions
        return True

    def _compact_route_store(self, *, extra_node_ids: list[int] | None = None) -> None:
        compaction_started = time.perf_counter()
        self.phase_timing_metrics["route_store_compaction_count"] = int(self.phase_timing_metrics["route_store_compaction_count"]) + 1
        retained: set[int] = set(extra_node_ids or [])
        for nodes in self.pending.values():
            retained.update(node.node_id for node in nodes)
        for accumulator in self.pending_accumulators.values():
            retained.update(accumulator.node_ids())
        retained.update(self.partial_action_cursors)
        for queue in self.bucket_resume_queues.values():
            retained.update(int(node_id) for node_id in queue)
        retained.update(int(route["terminal_node_id"]) for route in self.completed if "terminal_node_id" in route)
        if self.best_completed_search_route is not None:
            retained.add(int(self.best_completed_search_route["terminal_node_id"]))
        closure: set[int] = set()
        stack = list(retained)
        while stack:
            node_id = stack.pop()
            if node_id in closure or node_id not in self.route_store:
                continue
            closure.add(node_id)
            parent_id = self.route_store[node_id].get("parent_id")
            if parent_id is not None:
                stack.append(int(parent_id))
        self.route_store = {node_id: self.route_store[node_id] for node_id in sorted(closure)}
        self.phase_timing_metrics["route_store_compaction_seconds"] = float(self.phase_timing_metrics["route_store_compaction_seconds"]) + (time.perf_counter() - compaction_started)

    def _frontier_rel_path(self, bucket_index: int) -> Path:
        return self.frontier_root / f"bucket_{bucket_index:06d}.json.gz"

    def _update_peak_metrics(self, node: BeamNode | None = None) -> None:
        self.metric_update_count += 1
        self.peak_live_nodes = max(self.peak_live_nodes, self.live_node_count)
        self.peak_frontier_size = max(self.peak_frontier_size, self.live_node_count)
        self.peak_process_rss_bytes = max(self.peak_process_rss_bytes, _process_peak_rss_bytes())
        if node is not None:
            self.peak_serialized_payload_bytes = max(self.peak_serialized_payload_bytes, int(node.payload_size_bytes))

    def _update_peak_metrics_for_node(self, node: BeamNode) -> None:
        self._update_peak_metrics(node)

    def _wall_clock_exceeded(self, started: float) -> bool:
        limit = self.stage.get("wall_clock_limit_seconds")
        return limit is not None and (time.perf_counter() - started) >= float(limit)

    def _memory_budget_exceeded(self) -> bool:
        budget = self.stage.get("memory_budget_bytes")
        if budget is None:
            return False
        estimate = self._tracked_memory_estimate()
        return max(int(estimate["conservative_total_bytes"]), int(self.peak_process_rss_bytes)) >= int(budget)

    def _budget_limit_status(self, started: float, *, force: bool = False) -> str | None:
        if not force and self.limit_check_interval_expansions > 0 and self.expansions % self.limit_check_interval_expansions != 0:
            return None
        if self._wall_clock_exceeded(started):
            return "wall_clock_budget_exhausted"
        if self._memory_budget_exceeded():
            return "memory_budget_exhausted"
        return None

    def _tracked_memory_estimate(self) -> dict[str, Any]:
        contract = self.plan.get("memory_estimate_contract", {})
        route_store_bytes_per_edge = int(contract.get("route_store_bytes_per_edge", 256))
        scratch_bytes_per_node = int(contract.get("scratch_bytes_per_node", 512))
        completed_record_bytes = int(contract.get("completed_record_bytes", 4096))
        overhead_factor = float(contract.get("runtime_overhead_safety_factor", contract.get("safety_factor", 2.0)))
        live_payload_bytes = int(self.peak_live_nodes) * max(int(self.peak_serialized_payload_bytes), 1)
        accumulator_unique_nodes = sum(len(accumulator.best_by_fingerprint) for accumulator in self.pending_accumulators.values())
        accumulator_spilled_nodes = sum(int(accumulator.spilled_unique_fingerprint_count) for accumulator in self.pending_accumulators.values())
        accumulator_payload_bytes = accumulator_unique_nodes * max(int(self.peak_serialized_payload_bytes), 1)
        accumulator_index_bytes = accumulator_unique_nodes * int(contract.get("accumulator_index_bytes_per_node", 128))
        route_store_bytes = max(len(self.route_store), self.peak_live_nodes) * route_store_bytes_per_edge
        scratch_bytes = int(self.stage["beam_width"]) * scratch_bytes_per_node
        completed_bytes = len(self.completed) * completed_record_bytes
        subtotal = live_payload_bytes + accumulator_payload_bytes + accumulator_index_bytes + route_store_bytes + scratch_bytes + completed_bytes
        return {
            "schema_version": "beam_search_runtime_memory_estimate_v111",
            "payload_only_bytes": live_payload_bytes,
            "destination_accumulator_unique_nodes": accumulator_unique_nodes,
            "destination_accumulator_spilled_nodes_on_disk": accumulator_spilled_nodes,
            "destination_accumulator_payload_bytes": accumulator_payload_bytes,
            "destination_accumulator_index_bytes": accumulator_index_bytes,
            "route_store_bytes": route_store_bytes,
            "expansion_scratch_bytes": scratch_bytes,
            "completed_route_record_bytes": completed_bytes,
            "overhead_safety_factor": overhead_factor,
            "conservative_total_bytes": int(subtotal * overhead_factor),
            "configured_memory_budget_bytes": self.stage.get("memory_budget_bytes"),
        }

    def _frontier_bounds_payload(self) -> dict[str, Any]:
        live_budget = _live_node_budget(self.plan, self.stage)
        max_bucket_nodes = max((len(nodes) for nodes in self.pending.values()), default=0)
        accumulator_unique_counts = {
            str(bucket_index): len(accumulator.best_by_fingerprint) + int(accumulator.spilled_unique_fingerprint_count)
            for bucket_index, accumulator in sorted(self.pending_accumulators.items())
        }
        accumulator_memory_unique_counts = {
            str(bucket_index): len(accumulator.best_by_fingerprint)
            for bucket_index, accumulator in sorted(self.pending_accumulators.items())
        }
        max_accumulator_unique = max(accumulator_unique_counts.values(), default=0)
        max_accumulator_memory_unique = max(accumulator_memory_unique_counts.values(), default=0)
        accumulator_bound = _accumulator_unique_bound(self.stage)
        accumulator_in_memory_bound = _accumulator_in_memory_limit(self.stage)
        return {
            "schema_version": "beam_search_frontier_bounds_v111",
            "pending_bucket_node_bound": int(self.stage["beam_width"]),
            "live_node_budget": live_budget,
            "destination_accumulator_in_memory_unique_fingerprint_bound": accumulator_in_memory_bound,
            "destination_accumulator_unique_fingerprint_bound": accumulator_bound,
            "destination_accumulator_bucket_count": len(self.pending_accumulators),
            "destination_accumulator_total_unique_fingerprints": sum(accumulator_unique_counts.values()),
            "destination_accumulator_max_unique_fingerprints": max_accumulator_unique,
            "destination_accumulator_unique_fingerprints_by_bucket": accumulator_unique_counts,
            "destination_accumulator_max_in_memory_unique_fingerprints": max_accumulator_memory_unique,
            "destination_accumulator_in_memory_unique_fingerprints_by_bucket": accumulator_memory_unique_counts,
            "pending_bucket_count": len(self.pending),
            "max_pending_bucket_node_count": max_bucket_nodes,
            "live_node_count": self.live_node_count,
            "peak_live_nodes": self.peak_live_nodes,
            "peak_live_nodes_ge_live_node_count": self.peak_live_nodes >= self.live_node_count,
            "all_pending_buckets_within_bound": all(len(nodes) <= int(self.stage["beam_width"]) for nodes in self.pending.values()),
            "all_destination_accumulators_within_bound": max_accumulator_memory_unique <= accumulator_in_memory_bound,
            "live_nodes_within_bound": self.live_node_count <= live_budget,
        }

    def _assert_frontier_bounds(self) -> None:
        beam_width = int(self.stage["beam_width"])
        oversized = {bucket: len(nodes) for bucket, nodes in self.pending.items() if len(nodes) > beam_width}
        if oversized:
            raise RuntimeError(f"Beam pending bucket bound exceeded: {oversized}")
        live_budget = _live_node_budget(self.plan, self.stage)
        if self.live_node_count > live_budget:
            raise RuntimeError(f"Beam live-node budget exceeded: live={self.live_node_count} budget={live_budget}")
        accumulator_bound = _accumulator_in_memory_limit(self.stage)
        oversized_accumulators = {
            bucket: len(accumulator.best_by_fingerprint)
            for bucket, accumulator in self.pending_accumulators.items()
            if len(accumulator.best_by_fingerprint) > accumulator_bound
        }
        if oversized_accumulators:
            raise RuntimeError(f"Beam destination accumulator bound exceeded: {oversized_accumulators}")

    def _atomic_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, path)

    def _write_log(self, text: str) -> None:
        self.logs_root.mkdir(parents=True, exist_ok=True)
        with (self.logs_root / f"{self.stage_id}.log").open("a", encoding="utf-8") as file:
            file.write(text + "\n")


def _smoke_stage(max_expansions: int | None) -> dict[str, Any]:
    return {
        "stage_id": SMOKE_STAGE_ID,
        "combat_duration": 3.0,
        "time_bucket_width": 0.5,
        "beam_width": 64,
        "global_damage_quota": 32,
        "diversity_retention_quota": 32,
        "max_states_per_diversity_key": 4,
        "maximum_expansions": min(max_expansions or 2000, 2000),
        "wall_clock_limit_seconds": 120.0,
        "memory_budget_bytes": 536870912,
        "limit_check_interval_expansions": 64,
        "destination_accumulator_unique_fingerprint_bound": 1024,
    }


def _select_retained_batch(nodes: list[BeamNode], stage: dict[str, Any]) -> dict[str, Any]:
    best_by_fingerprint: dict[str, BeamNode] = {}
    duplicates = 0
    replacements = 0
    for node in nodes:
        existing = best_by_fingerprint.get(node.future_fingerprint)
        if existing is None:
            best_by_fingerprint[node.future_fingerprint] = node
            continue
        duplicates += 1
        if _node_order_key(node) < _node_order_key(existing):
            best_by_fingerprint[node.future_fingerprint] = node
            replacements += 1
    result = _select_retained_unique(list(best_by_fingerprint.values()), stage)
    result["metrics"]["exact_fingerprint_duplicates"] = duplicates
    result["metrics"]["better_duplicate_replacements"] = replacements
    return result


def _select_retained_unique(nodes: Iterable[BeamNode], stage: dict[str, Any]) -> dict[str, Any]:
    candidates = sorted(nodes, key=_node_order_key)
    global_quota = int(stage["global_damage_quota"])
    diversity_quota = int(stage["diversity_retention_quota"])
    beam_width = int(stage["beam_width"])
    max_per_key = int(stage["max_states_per_diversity_key"])
    retained: list[BeamNode] = candidates[:global_quota]
    retained_ids = {node.node_id for node in retained}
    per_key: dict[str, int] = {}
    for node in retained:
        per_key[node.diversity_key] = per_key.get(node.diversity_key, 0) + 1
    diversity_key_cap_rejections = 0
    diversity_quota_rejections = 0
    for node in candidates[global_quota:]:
        if len(retained) >= min(beam_width, global_quota + diversity_quota):
            diversity_quota_rejections += 1
            continue
        if node.node_id in retained_ids:
            continue
        count = per_key.get(node.diversity_key, 0)
        if count >= max_per_key:
            diversity_key_cap_rejections += 1
            continue
        retained.append(node)
        retained_ids.add(node.node_id)
        per_key[node.diversity_key] = count + 1
    before_width_trim = len(retained)
    retained = sorted(retained, key=_node_order_key)[:beam_width]
    final_beam_width_rejections = max(0, before_width_trim - len(retained))
    final_rejected_count = max(0, len(candidates) - len(retained))
    return {
        "retained": retained,
        "metrics": {
            "candidates_seen": len(nodes),
            "unique_fingerprint_count": len(candidates),
            "final_retained_count": len(retained),
            "candidates_outside_global_quota": max(0, len(candidates) - global_quota),
            "candidates_rejected_by_final_global_quota": max(0, len(candidates) - global_quota),
            "candidates_rejected_by_diversity_key_cap": diversity_key_cap_rejections,
            "candidates_rejected_by_diversity_quota": diversity_quota_rejections,
            "candidates_rejected_by_final_beam_width": final_beam_width_rejections,
            "final_rejected_count": final_rejected_count,
            "exact_fingerprint_duplicates": 0,
            "better_duplicate_replacements": 0,
        },
    }


def _accumulator_unique_bound(stage: dict[str, Any]) -> int:
    return int(stage.get("destination_accumulator_unique_fingerprint_bound", int(stage["beam_width"]) * 8))


def _accumulator_in_memory_limit(stage: dict[str, Any]) -> int:
    return int(stage.get("in_memory_accumulator_candidate_limit", _accumulator_unique_bound(stage)))


def _spill_stage_contract_sha256(stage: dict[str, Any]) -> str:
    stable = dict(stage)
    for key in ("maximum_expansions", "wall_clock_limit_seconds", "wall_clock_budget_seconds", "memory_budget_bytes", "result_scope"):
        stable.pop(key, None)
    return _json_sha256(stable)


def _canonical_output_root(plan: dict[str, Any], plan_path: Path | None = None) -> Path:
    relative = plan.get("output_contract", {}).get("canonical_output_root")
    project_root = _project_root_for_plan(plan_path) if plan_path is not None else ROOT
    return project_root / str(relative) if relative else CANONICAL_RESULTS_ROOT


def is_low_memory_execution_plan(plan: dict[str, Any]) -> bool:
    execution = plan.get("execution_contract")
    if isinstance(execution, dict) and "low_memory_32gb" in execution:
        return execution.get("low_memory_32gb") is True
    return plan.get("schema_version") in {LOWMEM_32GB_SCHEMA, V114_LOWMEM_32GB_SCHEMA}


def _project_root_for_plan(plan_path: Path) -> Path:
    resolved = plan_path.resolve()
    if resolved.parent.name == "data":
        return resolved.parent.parent
    return ROOT


def _process_peak_rss_bytes() -> int:
    """Best-effort peak resident-set measurement without a required dependency."""
    if os.name == "nt":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        try:
            get_current_process = ctypes.windll.kernel32.GetCurrentProcess
            get_current_process.restype = ctypes.c_void_p
            get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
            get_process_memory_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessMemoryCounters), ctypes.c_ulong]
            get_process_memory_info.restype = ctypes.c_int
            handle = get_current_process()
            if get_process_memory_info(handle, ctypes.byref(counters), counters.cb):
                return int(counters.PeakWorkingSetSize)
        except (AttributeError, OSError):
            return 0
        return 0
    try:
        import resource

        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return peak if os.uname().sysname == "Darwin" else peak * 1024
    except (AttributeError, ImportError, OSError):
        return 0


def _memory_estimate_for_stage(plan: dict[str, Any], stage: dict[str, Any]) -> dict[str, Any]:
    payload_guard = int(plan.get("state_payload_contract", {}).get("declared_payload_guard_bytes", 65536))
    beam_width = int(stage["beam_width"])
    contract = plan.get("memory_estimate_contract", {})
    derived = _derived_concurrent_bucket_bound(float(stage["time_bucket_width"]), int(contract.get("current_bucket_allowance", 1)), int(contract.get("bucket_safety_margin", 2)))
    concurrent_bucket_count = int(contract.get("concurrent_bucket_count", 0))
    if concurrent_bucket_count < derived["required_concurrent_bucket_count"]:
        raise ValueError(
            "memory_estimate_contract.concurrent_bucket_count "
            f"{concurrent_bucket_count} < derived required {derived['required_concurrent_bucket_count']}"
        )
    safety_factor = float(contract.get("safety_factor", 2.0))
    route_store_bytes_per_edge = int(contract.get("route_store_bytes_per_edge", 256))
    scratch_bytes_per_node = int(contract.get("scratch_bytes_per_node", 512))
    completed_record_bytes = int(contract.get("completed_record_bytes", 4096))
    accumulator_index_bytes_per_node = int(contract.get("accumulator_index_bytes_per_node", 128))
    live_node_budget = _live_node_budget(plan, stage)
    accumulator_unique_bound = _accumulator_unique_bound(stage)
    accumulator_node_budget = concurrent_bucket_count * accumulator_unique_bound
    payload_bytes = live_node_budget * payload_guard
    accumulator_payload_bytes = accumulator_node_budget * payload_guard
    accumulator_index_bytes = accumulator_node_budget * accumulator_index_bytes_per_node
    route_store_bytes = live_node_budget * route_store_bytes_per_edge
    scratch_bytes = live_node_budget * scratch_bytes_per_node
    completed_route_bytes = int(plan.get("completed_route_leaderboard_size", 128)) * completed_record_bytes
    total_without_safety = payload_bytes + accumulator_payload_bytes + accumulator_index_bytes + route_store_bytes + scratch_bytes + completed_route_bytes
    return {
        "schema_version": "beam_search_memory_estimate_v111",
        "stage_id": stage["stage_id"],
        "payload_guard_bytes_per_node": payload_guard,
        "beam_width": beam_width,
        "concurrent_bucket_count": concurrent_bucket_count,
        "derived_concurrent_bucket_bound": derived,
        "live_node_budget": live_node_budget,
        "pending_bucket_node_bound": beam_width,
        "destination_accumulator_unique_fingerprint_bound_per_bucket": accumulator_unique_bound,
        "destination_accumulator_node_budget": accumulator_node_budget,
        "live_node_budget_formula": "stage.beam_width * memory_estimate_contract.concurrent_bucket_count",
        "destination_bucket_retention": contract.get("destination_bucket_retention"),
        "limit_check_interval_expansions": int(stage.get("limit_check_interval_expansions", contract.get("limit_check_interval_expansions", 64))),
        "stage_wall_clock_limit_seconds": stage.get("wall_clock_limit_seconds"),
        "stage_memory_budget_bytes": stage.get("memory_budget_bytes"),
        "payload_bytes": payload_bytes,
        "destination_accumulator_payload_bytes": accumulator_payload_bytes,
        "destination_accumulator_index_bytes": accumulator_index_bytes,
        "route_store_bytes": route_store_bytes,
        "scratch_bytes": scratch_bytes,
        "completed_route_record_bytes": completed_route_bytes,
        "safety_factor": safety_factor,
        "conservative_total_bytes": int(total_without_safety * safety_factor),
        "policy": "payload_plus_concurrent_buckets_plus_route_store_plus_scratch_with_safety_factor",
    }


def _live_node_budget(plan: dict[str, Any], stage: dict[str, Any]) -> int:
    contract = plan.get("memory_estimate_contract", {})
    return int(stage["beam_width"]) * int(contract.get("concurrent_bucket_count", 1))


def _derived_concurrent_bucket_bound(time_bucket_width: float, current_bucket_allowance: int, safety_margin: int) -> dict[str, Any]:
    max_cost, action_id = _max_resolved_combat_time_cost()
    future_bucket_offsets = int(math.ceil(max_cost / float(time_bucket_width)))
    required = future_bucket_offsets + int(current_bucket_allowance) + int(safety_margin)
    return {
        "max_resolved_combat_time_cost": max_cost,
        "max_resolved_combat_time_cost_action_id": action_id,
        "time_bucket_width": float(time_bucket_width),
        "future_bucket_offsets": future_bucket_offsets,
        "current_bucket_allowance": int(current_bucket_allowance),
        "bucket_safety_margin": int(safety_margin),
        "required_concurrent_bucket_count": required,
    }


def _max_resolved_combat_time_cost() -> tuple[float, str]:
    candidates: list[tuple[float, str]] = []
    for rel in ("data/actions.json", "data/transition_actions.json"):
        path = ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.values() if isinstance(data, dict) else data
        for item in items:
            if not isinstance(item, dict):
                continue
            value = item.get("combat_time_cost", item.get("action_time"))
            if isinstance(value, (int, float)):
                candidates.append((float(value), str(item.get("id") or item.get("action_id") or "unknown")))
    if not candidates:
        raise ValueError("No action combat_time_cost/action_time values available for Beam memory bound")
    return max(candidates, key=lambda item: item[0])


def _node_order_key(node: BeamNode) -> tuple[float, float, int, str, str, int]:
    return (
        -float(node.total_damage),
        float(node.combat_time),
        int(node.action_count),
        node.future_fingerprint,
        node.lineage_tie_key or "",
        node.node_id,
    )


def _route_edge(node: BeamNode) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "parent_id": node.parent_id,
        "selected_action_id": node.selected_action_id,
        "resolved_action_id": node.resolved_action_id,
    }


def _leaderboard_payload(
    result: dict[str, Any], stage_id: str, *, result_scope: str | None = None,
    incumbent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": "beam_search_leaderboard_v111",
        "objective": "deterministic_120s_total_damage_only",
        "winner_selection": "final_total_damage_only",
        "route_similarity_objective": False,
        "completed_search_routes": result.get("completed_routes", []),
        "partial_frontier_diagnostics": result.get("best_partial_frontier_node"),
    }
    full_scope = result_scope == "completed_120s_project_comparison"
    if full_scope:
        candidates = [
            {
                "winner_kind": "beam_search_route",
                "total_damage": route["total_damage"],
                "dps": route["total_damage"] / 120.0,
                "declared_order": index + 1,
                "route": route,
            }
            for index, route in enumerate(result.get("completed_routes", []))
        ]
        if incumbent is None:
            raise ValueError("Completed-120s project reporting requires a validated incumbent")
        payload["project_comparison_incumbent"] = incumbent
        payload["historical_verified_bc_reference"] = historical_verified_bc_reference()
        payload["calibration_only_no_project_winner"] = False
        payload["partial_nodes_excluded_from_final_winner"] = True
        payload["winner"] = select_damage_only_winner(candidates, incumbent=incumbent)
    else:
        payload["calibration_only_no_project_winner"] = True
        payload["winner"] = None
    return payload


def _best_route_payload(result: dict[str, Any], stage_id: str, *, result_scope: str | None = None, incumbent: dict[str, Any] | None = None) -> dict[str, Any]:
    leaderboard = _leaderboard_payload(result, stage_id, result_scope=result_scope, incumbent=incumbent)
    if result_scope == "completed_120s_project_comparison":
        return {
            "schema_version": "beam_search_best_route_v111",
            "winner": leaderboard["winner"],
            "partial_nodes_excluded_from_final_winner": True,
        }
    return {
        "schema_version": "beam_search_best_route_v111",
        "calibration_only_no_project_winner": True,
        "best_completed_search_route": result.get("best_completed_search_route"),
        "best_partial_frontier_node": result.get("best_partial_frontier_node"),
    }


def _summary_payload(result: dict[str, Any], stage_id: str, *, result_scope: str | None = None, incumbent: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "beam_search_final_summary_v111",
        "stage_id": result["stage_id"],
        "status": result["status"],
        "global_optimum_proven": False,
        "route_similarity_usage": "diagnostic_only_not_used_for_winner_selection",
        "result_scope": result_scope,
        "calibration_only_no_project_winner": result_scope != "completed_120s_project_comparison",
        "partial_nodes_excluded_from_final_winner": result_scope == "completed_120s_project_comparison",
        "winner": _leaderboard_payload(result, stage_id, result_scope=result_scope, incumbent=incumbent)["winner"],
        "expansions": result["expansions"],
        "metrics": {
            "peak_frontier_size": result["peak_frontier_size"],
            "peak_live_nodes": result["peak_live_nodes"],
            "peak_serialized_payload_bytes": result["peak_serialized_payload_bytes"],
            "estimated_peak_memory_bytes": result["estimated_peak_memory_bytes"],
            "peak_process_rss_bytes": result.get("peak_process_rss_bytes"),
            "expansions_per_second": result["expansions_per_second"],
            "invocation_expansions_per_second": result["invocation_expansions_per_second"],
            "cumulative_expansions_per_second": result["cumulative_expansions_per_second"],
        },
    }


def _is_full_stage(stage_id: str) -> bool:
    """Legacy classification helper; new plans must use the explicit result_scope."""
    return stage_id in {"full_120s", "full_120s_lowmem_32gb", "full_120s_lowmem_32gb_v114"}


def _resume_extension_plan_compatible(state: dict[str, Any], plan: dict[str, Any]) -> bool:
    contract = plan.get("resume_extension_contract") or {}
    if contract.get("enabled") is not True:
        return False
    if state.get("plan_sha256") != contract.get("source_plan_sha256"):
        return False
    if state.get("stage", {}).get("stage_id") != contract.get("source_stage_id"):
        return False
    if int(state.get("expansions", -1)) != int(contract.get("source_checkpoint_expansions", -2)):
        return False
    current = plan.get("stages", [None])[0]
    if not isinstance(current, dict):
        return False
    return extension_stage_compatible(state.get("stage", {}), current, contract)


def _json_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _resume_stage_compatible(saved: dict[str, Any], current: dict[str, Any]) -> bool:
    saved_compare = dict(saved)
    current_compare = dict(current)
    saved_limit = int(saved_compare.pop("maximum_expansions"))
    current_limit = int(current_compare.pop("maximum_expansions"))
    for key in ("wall_clock_limit_seconds", "memory_budget_bytes"):
        saved_budget = saved_compare.pop(key, None)
        current_budget = current_compare.pop(key, None)
        if saved_budget is not None:
            if current_budget is None or float(current_budget) < float(saved_budget):
                return False
    return saved_compare == current_compare and current_limit >= saved_limit


def _next_completion_order_from_records(records: list[dict[str, Any]]) -> int:
    return max((int(item.get("completion_order", 0)) for item in records), default=0) + 1


def _project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _portable_spill_path(path: Path, output_root: Path | None) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        if output_root is None:
            raise ValueError(f"Streaming spill path is outside the project without an output root: {resolved}")
        try:
            return resolved.relative_to(output_root.resolve()).as_posix()
        except ValueError as error:
            raise ValueError(f"Streaming spill path is outside its output root: {resolved}") from error


def _resolve_stored_path(path_text: str, output_root: Path | None = None) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    root_candidate = ROOT / path
    if root_candidate.exists():
        return root_candidate
    if output_root is not None:
        output_candidate = output_root / path
        if output_candidate.exists():
            return output_candidate
    return root_candidate
