from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_destination_bucket_test_utils import make_node
from search.beam_search import DestinationBucketAccumulator


def main() -> None:
    stage = {
        "stage_id": "metrics",
        "combat_duration": 3.0,
        "time_bucket_width": 0.5,
        "beam_width": 3,
        "global_damage_quota": 1,
        "diversity_retention_quota": 2,
        "max_states_per_diversity_key": 1,
        "maximum_expansions": 1,
        "destination_accumulator_unique_fingerprint_bound": 64,
    }
    nodes = [
        make_node(1, damage=10.0, key="K1", fingerprint="same"),
        make_node(2, damage=5.0, key="K1", fingerprint="same"),
        make_node(3, damage=20.0, key="K1", fingerprint="same"),
        make_node(4, damage=9.0, key="K1"),
        make_node(5, damage=8.0, key="K2"),
        make_node(6, damage=7.0, key="K3"),
        make_node(7, damage=6.0, key="K4"),
    ]
    accumulator = DestinationBucketAccumulator(bucket_index=3, stage=stage)
    for node in nodes:
        accumulator.add(node)
    metrics = accumulator.metrics()
    assert metrics["candidates_seen"] == 7
    assert metrics["unique_fingerprint_count"] == 5
    assert metrics["exact_fingerprint_duplicates"] == 2
    assert metrics["better_duplicate_replacements"] == 1
    assert metrics["final_retained_count"] == 3
    assert metrics["final_rejected_count"] == 2
    assert metrics["rejected_by_diversity_key_cap"] == 1
    assert metrics["rejected_because_diversity_quota_filled"] == 1
    assert metrics["candidates_seen"] == metrics["exact_fingerprint_duplicates"] + metrics["unique_fingerprint_count"]
    assert metrics["unique_fingerprint_count"] == metrics["final_retained_count"] + metrics["final_rejected_count"]
    print("beam_search_accumulator_metrics_contract_smoke_test ok")


if __name__ == "__main__":
    main()
