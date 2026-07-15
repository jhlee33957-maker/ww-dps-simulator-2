from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mcts_v117_test_utils import plan_and_stage
from search.mcts_search import MCTSSearch
from search.search_state_codec import full_node_state_fingerprint


def runner_with_chain(depth: int, *, zero_time: bool) -> tuple[MCTSSearch, tempfile.TemporaryDirectory[str]]:
    temporary = tempfile.TemporaryDirectory(prefix="mcts_selection_guard_")
    plan, stage = plan_and_stage(simulations=1, combat_duration=120.0, maximum_nodes=max(depth + 4, 520))
    runner = MCTSSearch(
        plan=plan,
        stage=stage,
        output_root=Path(temporary.name),
        max_simulations=1,
        allow_test_output_root=True,
    )
    runner._initialize_new()
    runner.tree.legal_action_mask[0] = 1
    root_ref = int(runner.tree.snapshot_ref[0])
    full_fp = runner.tree.full_state_fingerprint[0].decode("ascii")
    future_fp = runner.tree.future_state_fingerprint[0].decode("ascii")
    parent = 0
    for index in range(depth):
        combat_time = 0.0 if zero_time else float(index + 1)
        parent = runner.tree.add_node(
            parent_id=parent,
            action_slot=0,
            legal_slots=[0],
            terminal=False,
            invalid=False,
            snapshot_ref=root_ref,
            total_damage=0.0,
            combat_time=combat_time,
            current_time=combat_time,
            full_fingerprint=full_fp,
            future_fingerprint=future_fp,
        )
    assert full_node_state_fingerprint(runner.template) == full_fp
    return runner, temporary
