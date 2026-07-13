from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_destination_bucket_test_utils import STAGE, make_node, retained_ids
from search.beam_search import DestinationBucketAccumulator, _select_retained_batch


def main() -> None:
    stage = STAGE | {"beam_width": 1, "global_damage_quota": 1, "diversity_retention_quota": 0}
    left = make_node(100, damage=10.0, key="K", fingerprint="same")
    right = make_node(1, damage=10.0, key="K", fingerprint="same")
    left.lineage_tie_key = "aaa"
    right.lineage_tie_key = "zzz"
    expected = retained_ids(_select_retained_batch([left, right], stage)["retained"])
    assert expected == retained_ids(_select_retained_batch([right, left], stage)["retained"])
    accumulator = DestinationBucketAccumulator(bucket_index=1, stage=stage)
    accumulator.add(right)
    accumulator.add(left)
    assert retained_ids(accumulator.retained_nodes()) == expected
    assert expected == [left.node_id]
    print("beam_search_duplicate_lineage_tie_smoke_test ok")


if __name__ == "__main__":
    main()
