from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_tree import MCTSTree, allowed_children, deterministic_action_rank, uct_score


def main() -> None:
    assert allowed_children(0, 25) == 1 and allowed_children(1, 25) == 2 and allowed_children(4, 25) == 4 and allowed_children(169, 25) == 25
    assert math.isinf(uct_score(10, 0, 0.0))
    expected = 0.5 + math.sqrt(2.0) * math.sqrt(math.log(10) / 2)
    assert abs(uct_score(10, 2, 1.0) - expected) < 1e-15
    actions = tuple(f"a{i}" for i in range(25)); tree = MCTSTree(8)
    tree.add_node(parent_id=-1, action_slot=-1, legal_slots=[0, 1], terminal=False, invalid=False, snapshot_ref=0,
                  total_damage=0, combat_time=0, current_time=0, full_fingerprint="a" * 64, future_fingerprint="b" * 64)
    for slot in (0, 1):
        tree.add_node(parent_id=0, action_slot=slot, legal_slots=[], terminal=False, invalid=False, snapshot_ref=-1,
                      total_damage=0, combat_time=1, current_time=1, full_fingerprint=chr(99 + slot) * 64, future_fingerprint="d" * 64)
    tree.visits[0] = 3; tree.visits[1] = 1; tree.value_sum[1] = 0.2
    assert tree.choose_child(0, [0, 1], seed=117001, action_ids=actions) == 2
    first = sorted(range(25), key=lambda slot: deterministic_action_rank(117001, "a" * 64, actions[slot]))
    assert len(set(first)) == 25
    print("mcts_uct_progressive_widening_smoke_test ok")


if __name__ == "__main__": main()
