from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_destination_bucket_test_utils import accumulator_ids, counterexample_nodes, one_shot_ids  # noqa: E402


def main() -> None:
    parts = counterexample_nodes()
    rare = parts["rare"]
    nodes = [*parts["global"], *parts["diversity"], rare, *parts["late_global"]]
    expected = one_shot_ids(nodes)
    retained = accumulator_ids(nodes)
    assert len(expected) == 1017
    assert len(retained) == len(expected)
    assert retained == expected
    assert rare.node_id in retained
    print("beam_search_diversity_quota_fill_smoke_test ok")


if __name__ == "__main__":
    main()
