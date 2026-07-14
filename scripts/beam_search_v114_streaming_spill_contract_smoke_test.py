from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import search.beam_search as beam_search
from scripts.beam_search_destination_bucket_test_utils import make_node, retained_ids
from search.beam_plan import (
    STREAMING_ACCUMULATOR_SPILL_FORMAT,
    V114_LOWMEM_32GB_PLAN_PATH,
    load_plan,
    resolve_accumulator_spill_format,
    sha256_file,
    validate_plan,
)
from search.beam_spill import STREAMING_CHUNK_SCHEMA, validate_accumulator_chunk


def _nodes() -> list:
    nodes = [
        make_node(index, damage=100_000.0 - index, key=f"key-{index % 450}")
        for index in range(1, 4206)
    ]
    nodes.extend(
        make_node(
            10_000 + index,
            damage=200_000.0 + index,
            key=f"key-{index % 450}",
            fingerprint=f"fp-{index}",
        )
        for index in range(1, 26)
    )
    return nodes


def _build(stage: dict, nodes: list, root: Path, plan_sha: str) -> beam_search.DestinationBucketAccumulator:
    accumulator = beam_search.DestinationBucketAccumulator(
        bucket_index=7,
        stage=stage,
        max_unique_fingerprints=4096,
        spill_root=root,
        output_root=root,
        plan_sha256=plan_sha,
    )
    assert accumulator.streaming_spill is True
    assert accumulator.accumulator_spill_format == STREAMING_ACCUMULATOR_SPILL_FORMAT
    for node in nodes:
        accumulator.add(node)
    accumulator.spill_current_chunk()
    return accumulator


def main() -> int:
    plan = load_plan(V114_LOWMEM_32GB_PLAN_PATH)
    validation = validate_plan(plan, plan_path=V114_LOWMEM_32GB_PLAN_PATH)
    stage = copy.deepcopy(plan["stages"][0])
    assert stage["stage_id"] == "full_120s_lowmem_32gb_v114"
    assert resolve_accumulator_spill_format(stage) == STREAMING_ACCUMULATOR_SPILL_FORMAT
    assert validation["stage_accumulator_spill_formats"][stage["stage_id"]] == STREAMING_ACCUMULATOR_SPILL_FORMAT
    nodes = _nodes()
    assert len(nodes) > 4096
    authoritative = beam_search._select_retained_batch(nodes, stage)
    authoritative_ids = retained_ids(authoritative["retained"])
    plan_sha = sha256_file(V114_LOWMEM_32GB_PLAN_PATH)
    original_writer = beam_search.write_json_gz

    def forbidden_monolithic_writer(*args: object, **kwargs: object) -> str:
        raise AssertionError("actual v114 stage called the generic monolithic JSON-gzip writer")

    with tempfile.TemporaryDirectory(prefix="beam-v114-streaming-contract-") as temporary:
        root = Path(temporary)
        beam_search.write_json_gz = forbidden_monolithic_writer
        try:
            first = _build(stage, nodes, root / "first", plan_sha)
            second = _build(stage, nodes, root / "second", plan_sha)
            reversed_accumulator = _build(stage, list(reversed(nodes)), root / "reversed", plan_sha)

            left = beam_search.DestinationBucketAccumulator(
                bucket_index=7,
                stage=stage,
                max_unique_fingerprints=4096,
                spill_root=root / "partitioned",
                output_root=root / "partitioned",
                plan_sha256=plan_sha,
            )
            right = beam_search.DestinationBucketAccumulator(
                bucket_index=7,
                stage=stage,
                max_unique_fingerprints=4096,
                spill_root=root / "partitioned-right",
                output_root=root / "partitioned-right",
                plan_sha256=plan_sha,
            )
            for node in nodes[::2]:
                left.add(node)
            for node in nodes[1::2]:
                right.add(node)
            left.merge(right)
            left.spill_current_chunk()
        finally:
            beam_search.write_json_gz = original_writer

        for accumulator in (first, second, reversed_accumulator, left):
            assert accumulator.spill_chunks
            assert all(entry["schema_version"] == STREAMING_CHUNK_SCHEMA for entry in accumulator.spill_chunks)
            for entry in accumulator.spill_chunks:
                validated = validate_accumulator_chunk(
                    accumulator.output_root / entry["path"],
                    entry,
                    expected_plan_sha256=plan_sha,
                    expected_stage_id=stage["stage_id"],
                    expected_stage_contract_sha256=accumulator.stage_contract_sha256,
                )
                assert validated["candidate_count"] == entry["candidate_count"]

        assert [entry["sha256"] for entry in first.spill_chunks] == [
            entry["sha256"] for entry in second.spill_chunks
        ]
        first_retained = retained_ids(first.retained_nodes())
        assert first_retained == authoritative_ids
        assert retained_ids(second.retained_nodes()) == authoritative_ids
        assert retained_ids(reversed_accumulator.retained_nodes()) == authoritative_ids
        assert retained_ids(left.retained_nodes()) == authoritative_ids

        metrics = first.metrics()
        assert metrics["peak_spill_serialization_buffer_bytes"] > 0
        assert metrics["peak_spill_restore_buffer_bytes"] > 0
        assert metrics["peak_spill_chunk_uncompressed_bytes"] > metrics["peak_spill_serialization_buffer_bytes"]
        assert metrics["peak_spill_serialization_buffer_bytes"] < 1024 * 1024
        assert metrics["peak_spill_restore_buffer_bytes"] < 1024 * 1024
        assert metrics["candidates_seen"] == (
            metrics["exact_fingerprint_duplicates"] + metrics["unique_fingerprint_count"]
        )
        assert metrics["better_duplicate_replacements"] >= 25

        resumed = beam_search.DestinationBucketAccumulator.from_json(
            first.to_json(),
            stage=stage,
            spill_root=first.spill_root,
            output_root=first.output_root,
            plan_sha256=plan_sha,
            stage_contract_sha256=first.stage_contract_sha256,
        )
        assert retained_ids(resumed.retained_nodes()) == authoritative_ids
        assert resumed.metrics()["peak_spill_restore_buffer_bytes"] > 0

    print("beam_search_v114_streaming_spill_contract_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
