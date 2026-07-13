from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_search import DestinationBucketAccumulator  # noqa: E402
from scripts.beam_search_destination_bucket_test_utils import STAGE, counterexample_nodes, one_shot_ids, retained_ids  # noqa: E402


def main() -> None:
    parts = counterexample_nodes()
    nodes = [*parts["global"], *parts["diversity"], parts["rare"], *parts["late_global"]]
    expected = one_shot_ids(nodes)
    partitions = [nodes[:200], nodes[200:700], nodes[700:900], nodes[900:]]
    for order in ([0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2]):
        merged = DestinationBucketAccumulator(bucket_index=7, stage=STAGE)
        for partition_index in order:
            part_accumulator = DestinationBucketAccumulator(bucket_index=7, stage=STAGE)
            for node in partitions[partition_index]:
                part_accumulator.add(node)
            merged.merge(part_accumulator)
        assert retained_ids(merged.retained_nodes()) == expected
    print("beam_search_destination_bucket_partition_merge_smoke_test ok")


if __name__ == "__main__":
    main()
