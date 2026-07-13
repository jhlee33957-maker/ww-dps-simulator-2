from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_destination_bucket_test_utils import accumulator_ids, counterexample_nodes, one_shot_ids  # noqa: E402


def main() -> None:
    parts = counterexample_nodes()
    global_nodes = list(parts["global"])
    diversity_nodes = list(parts["diversity"])
    rare = parts["rare"]
    late_global = list(parts["late_global"])
    all_nodes = [*global_nodes, *diversity_nodes, rare, *late_global]
    expected = one_shot_ids(all_nodes)
    rare_before = accumulator_ids([*global_nodes, *diversity_nodes, rare, *late_global])
    rare_after = accumulator_ids([*global_nodes, *diversity_nodes, *late_global, rare])
    reversed_order = accumulator_ids(list(reversed(all_nodes)))
    assert rare.node_id in expected
    assert rare_before == expected
    assert rare_after == expected
    assert reversed_order == expected
    assert len(expected) == 1017
    print("beam_search_destination_bucket_order_independence_smoke_test ok")


if __name__ == "__main__":
    main()
