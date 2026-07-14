from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from search.beam_state import BeamNode


STREAMING_CHUNK_SCHEMA = "beam_search_accumulator_chunk_jsonl_gzip_v113"
STREAMING_CHUNK_FORMAT = "deterministic_gzip_json_lines"


def sha256_file_streaming(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_accumulator_chunk_streaming(
    path: Path,
    nodes: Sequence[BeamNode],
    *,
    bucket_index: int,
    chunk_index: int,
    plan_sha256: str,
    stage_id: str,
    stage_contract_sha256: str,
) -> dict[str, Any]:
    """Atomically write a deterministic gzip JSON-lines chunk one node at a time."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    header = {
        "record_type": "header",
        "schema_version": STREAMING_CHUNK_SCHEMA,
        "format": STREAMING_CHUNK_FORMAT,
        "bucket_index": int(bucket_index),
        "chunk_index": int(chunk_index),
        "candidate_count": len(nodes),
        "plan_sha256": str(plan_sha256),
        "stage_id": str(stage_id),
        "stage_contract_sha256": str(stage_contract_sha256),
    }
    uncompressed_bytes = 0
    max_serialization_buffer_bytes = 0
    try:
        with temp.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=6, mtime=0) as compressed:
                line = _json_line(header)
                compressed.write(line)
                uncompressed_bytes += len(line)
                max_serialization_buffer_bytes = len(line)
                for node in nodes:
                    line = _json_line({"record_type": "node", "node": node.to_json()})
                    compressed.write(line)
                    uncompressed_bytes += len(line)
                    max_serialization_buffer_bytes = max(max_serialization_buffer_bytes, len(line))
        sha256 = sha256_file_streaming(temp)
        compressed_bytes = temp.stat().st_size
        os.replace(temp, path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return {
        **header,
        "path": path.as_posix(),
        "sha256": sha256,
        "unique_fingerprint_count": len(nodes),
        "node_ids": [node.node_id for node in nodes],
        "compressed_bytes": compressed_bytes,
        "uncompressed_bytes": uncompressed_bytes,
        "max_serialization_buffer_bytes": max_serialization_buffer_bytes,
    }


def iter_accumulator_chunk_nodes(
    path: Path,
    entry: dict[str, Any],
    *,
    expected_plan_sha256: str,
    expected_stage_id: str,
    expected_stage_contract_sha256: str,
    metrics: dict[str, int] | None = None,
) -> Iterator[BeamNode]:
    """Validate and stream one BeamNode per JSON line without whole-file reads."""
    pass_started = time.perf_counter()
    sha_started = time.perf_counter()
    actual_sha256 = sha256_file_streaming(path)
    sha_elapsed = time.perf_counter() - sha_started
    if metrics is not None:
        metrics["sha_validation_count"] = int(metrics.get("sha_validation_count", 0)) + 1
        metrics["sha_validation_seconds"] = float(metrics.get("sha_validation_seconds", 0.0)) + sha_elapsed
        metrics["restore_pass_count"] = int(metrics.get("restore_pass_count", 0)) + 1
    if actual_sha256 != entry.get("sha256"):
        raise ValueError(f"Accumulator spill hash mismatch: {path}")
    count = 0
    restore_peak = 0
    try:
        with gzip.open(path, "rb") as compressed:
            first = compressed.readline()
            restore_peak = max(restore_peak, len(first))
            if not first:
                raise ValueError(f"Accumulator spill is empty: {path}")
            header = _parse_line(first, path)
            expected_header = {
                "record_type": "header",
                "schema_version": STREAMING_CHUNK_SCHEMA,
                "format": STREAMING_CHUNK_FORMAT,
                "bucket_index": int(entry["bucket_index"]),
                "chunk_index": int(entry["chunk_index"]),
                "candidate_count": int(entry["candidate_count"]),
                "plan_sha256": expected_plan_sha256,
                "stage_id": expected_stage_id,
                "stage_contract_sha256": expected_stage_contract_sha256,
            }
            if header != expected_header:
                raise ValueError(f"Accumulator spill header mismatch: {path}")
            for raw_line in compressed:
                restore_peak = max(restore_peak, len(raw_line))
                record = _parse_line(raw_line, path)
                if set(record) != {"record_type", "node"} or record.get("record_type") != "node":
                    raise ValueError(f"Accumulator spill node record mismatch: {path}")
                count += 1
                yield BeamNode.from_json(record["node"])
        if count != int(entry["candidate_count"]):
            raise ValueError(f"Accumulator spill count mismatch: {path}: {count} != {entry['candidate_count']}")
    finally:
        if metrics is not None:
            metrics["restore_node_count"] = int(metrics.get("restore_node_count", 0)) + count
            metrics["restore_seconds"] = float(metrics.get("restore_seconds", 0.0)) + (time.perf_counter() - pass_started)
            metrics["max_restore_buffer_bytes"] = max(int(metrics.get("max_restore_buffer_bytes", 0)), restore_peak)


def validate_accumulator_chunk(
    path: Path,
    entry: dict[str, Any],
    *,
    expected_plan_sha256: str,
    expected_stage_id: str,
    expected_stage_contract_sha256: str,
) -> dict[str, int]:
    metrics: dict[str, int] = {}
    count = sum(
        1
        for _ in iter_accumulator_chunk_nodes(
            path,
            entry,
            expected_plan_sha256=expected_plan_sha256,
            expected_stage_id=expected_stage_id,
            expected_stage_contract_sha256=expected_stage_contract_sha256,
            metrics=metrics,
        )
    )
    return {"candidate_count": count, **metrics}


def _json_line(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _parse_line(raw_line: bytes, path: Path) -> dict[str, Any]:
    try:
        value = json.loads(raw_line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid accumulator spill JSON line: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Accumulator spill record must be an object: {path}")
    return value
