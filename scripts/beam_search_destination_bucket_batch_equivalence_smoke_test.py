from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_destination_bucket_test_utils import STAGE, accumulator_ids, make_node, one_shot_ids  # noqa: E402


def main() -> None:
    nodes = _candidate_set()
    expected = one_shot_ids(nodes)
    permutations = [
        nodes,
        list(reversed(nodes)),
        nodes[::2] + nodes[1::2],
        sorted(nodes, key=lambda node: (node.diversity_key, -node.total_damage, node.node_id)),
    ]
    for permutation in permutations:
        assert accumulator_ids(permutation) == expected
    assert len(expected) <= STAGE["beam_width"]
    print("beam_search_destination_bucket_batch_equivalence_smoke_test ok")


def _candidate_set():
    nodes = []
    node_id = 1
    for key_index in range(90):
        key = f"K{key_index:02d}"
        for slot in range(12):
            nodes.append(make_node(node_id, damage=10_000.0 - key_index * 10.0 - slot, key=key))
            node_id += 1
    duplicate = make_node(node_id, damage=1.0, key="DUP", fingerprint="dup-fp")
    nodes.append(duplicate)
    node_id += 1
    better_duplicate = make_node(node_id, damage=20_000.0, key="DUP", fingerprint="dup-fp")
    nodes.append(better_duplicate)
    node_id += 1
    for tie in range(10):
        nodes.append(make_node(node_id, damage=7777.0, key="TIE", fingerprint=f"tie-{tie}"))
        node_id += 1
    return nodes


if __name__ == "__main__":
    main()
