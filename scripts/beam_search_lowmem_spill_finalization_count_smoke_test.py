from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_destination_bucket_test_utils import make_node, retained_ids
from scripts.beam_search_lowmem_spill_streaming_smoke_test import PLAN_SHA, STAGE
from search.beam_search import DestinationBucketAccumulator, _select_retained_batch


def main() -> int:
    nodes = [make_node(index, damage=50_000.0 - index, key=f"key-{index % 400}") for index in range(1, 4202)]
    authoritative = retained_ids(_select_retained_batch(nodes, STAGE)["retained"])
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        accumulator = DestinationBucketAccumulator(
            bucket_index=9,
            stage=STAGE,
            max_unique_fingerprints=4096,
            spill_root=root,
            output_root=root,
            plan_sha256=PLAN_SHA,
        )
        for node in nodes:
            accumulator.add(node)
        accumulator.spill_current_chunk()
        before = accumulator.cheap_metrics()
        assert before["spill_write_count"] == 2
        assert before["spill_restore_pass_count"] == 0
        assert before["full_accumulator_finalization_count"] == 0
        assert before["finalization_needed"] is True

        assert retained_ids(accumulator.retained_nodes()) == authoritative
        after = accumulator.cheap_metrics()
        assert after["spill_restore_pass_count"] == 2
        assert after["spill_restore_nodes_streamed"] == len(nodes)
        assert after["full_accumulator_finalization_count"] == 1
        assert after["finalization_needed"] is False

        assert retained_ids(accumulator.retained_nodes()) == authoritative
        assert accumulator.metrics()["full_accumulator_finalization_count"] == 1
        cached = accumulator.cheap_metrics()
        assert cached["spill_restore_pass_count"] == 2
        assert cached["spill_restore_nodes_streamed"] == len(nodes)
    print("beam_search_lowmem_spill_finalization_count_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
