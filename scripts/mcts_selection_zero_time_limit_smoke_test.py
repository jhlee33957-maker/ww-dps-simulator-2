from __future__ import annotations

from mcts_selection_guard_test_support import runner_with_chain
from search.search_state_codec import full_node_state_fingerprint


def main() -> None:
    runner, temporary = runner_with_chain(33, zero_time=True)
    try:
        before_nodes = runner.tree.node_count
        template_fp = full_node_state_fingerprint(runner.template)
        runner._simulate_once()
        assert runner.tree.node_count == before_nodes
        assert runner.invalid_rollout_counts == {
            "consecutive_zero_combat_time_actions_exceeded_during_selection": 1
        }
        assert full_node_state_fingerprint(runner.template) == template_fp
        print("mcts_selection_zero_time_limit_smoke_test ok allowed=32 rejected_tail=33")
    finally:
        temporary.cleanup()


if __name__ == "__main__":
    main()
