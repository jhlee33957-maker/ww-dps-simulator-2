from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import search.beam_search as beam_search
from scripts.beam_search_destination_bucket_test_utils import make_node, retained_ids
from search.beam_spill import STREAMING_CHUNK_SCHEMA, validate_accumulator_chunk


STAGE = {
    "stage_id": "full_120s_lowmem_32gb",
    "combat_duration": 120.0,
    "time_bucket_width": 0.5,
    "beam_width": 1792,
    "global_damage_quota": 896,
    "diversity_retention_quota": 896,
    "max_states_per_diversity_key": 8,
    "maximum_expansions": 5000000,
    "destination_accumulator_unique_fingerprint_bound": 16384,
    "in_memory_accumulator_candidate_limit": 4096,
}
PLAN_SHA = "streaming-spill-contract-test-plan"


def main() -> int:
    nodes = [make_node(index, damage=50_000.0 - index, key=f"key-{index % 400}") for index in range(1, 4202)]
    authoritative = retained_ids(beam_search._select_retained_batch(nodes, STAGE)["retained"])
    original_writer = beam_search.write_json_gz

    def forbidden_monolithic_writer(*args: object, **kwargs: object) -> str:
        raise AssertionError("low-memory spill called the monolithic JSON gzip writer")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        beam_search.write_json_gz = forbidden_monolithic_writer
        try:
            accumulator = beam_search.DestinationBucketAccumulator(
                bucket_index=7,
                stage=STAGE,
                max_unique_fingerprints=4096,
                spill_root=root,
                output_root=root,
                plan_sha256=PLAN_SHA,
            )
            for node in nodes:
                accumulator.add(node)
            accumulator.spill_current_chunk()
        finally:
            beam_search.write_json_gz = original_writer
        assert len(accumulator.spill_chunks) == 2
        assert accumulator.spill_chunks[0]["candidate_count"] == 4096
        assert all(entry["schema_version"] == STREAMING_CHUNK_SCHEMA for entry in accumulator.spill_chunks)
        assert all(not Path(entry["path"]).is_absolute() for entry in accumulator.spill_chunks)
        for entry in accumulator.spill_chunks:
            validated = validate_accumulator_chunk(
                root / entry["path"],
                entry,
                expected_plan_sha256=PLAN_SHA,
                expected_stage_id=STAGE["stage_id"],
                expected_stage_contract_sha256=accumulator.stage_contract_sha256,
            )
            assert validated["candidate_count"] == entry["candidate_count"]
        retained = retained_ids(accumulator.retained_nodes())
        assert retained == authoritative
        metrics = accumulator.metrics()
        assert metrics["peak_spill_serialization_buffer_bytes"] < 1024 * 1024
        assert metrics["peak_spill_restore_buffer_bytes"] < 1024 * 1024
        assert metrics["peak_finalization_unique_set_bytes"] < 64 * 1024 * 1024
        assert metrics["peak_final_sort_list_bytes"] < 1024 * 1024
        assert metrics["peak_spill_chunk_uncompressed_bytes"] > metrics["peak_spill_serialization_buffer_bytes"]
        payload = accumulator.to_json()
        resumed = beam_search.DestinationBucketAccumulator.from_json(
            payload,
            stage=STAGE,
            spill_root=root,
            output_root=root,
            plan_sha256=PLAN_SHA,
            stage_contract_sha256=accumulator.stage_contract_sha256,
        )
        assert retained_ids(resumed.retained_nodes()) == authoritative
        assert resumed.metrics()["exact_fingerprint_duplicates"] == metrics["exact_fingerprint_duplicates"]
        second = beam_search.DestinationBucketAccumulator(
            bucket_index=7,
            stage=STAGE,
            max_unique_fingerprints=4096,
            spill_root=root / "repeat",
            output_root=root / "repeat",
            plan_sha256=PLAN_SHA,
            stage_contract_sha256=accumulator.stage_contract_sha256,
        )
        for node in nodes[:4096]:
            second.add(node)
        repeat_entry = second.spill_current_chunk()
        assert repeat_entry is not None
        assert repeat_entry["sha256"] == accumulator.spill_chunks[0]["sha256"]
    print("beam_search_lowmem_spill_streaming_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
