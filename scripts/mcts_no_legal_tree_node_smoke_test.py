from __future__ import annotations

from mcts_selection_guard_test_support import runner_with_chain
from search.search_state_codec import full_node_state_fingerprint


def main() -> None:
    runner, temporary = runner_with_chain(0, zero_time=False)
    try:
        runner.tree.legal_action_mask[0] = 0
        before_nodes = runner.tree.node_count
        template_fp = full_node_state_fingerprint(runner.template)
        runner._simulate_once()
        assert runner.tree.node_count == before_nodes == 1
        assert runner.invalid_rollout_counts == {"no_legal_policy_action_at_tree_node": 1}
        assert full_node_state_fingerprint(runner.template) == template_fp
        print("mcts_no_legal_tree_node_smoke_test ok invalid_diagnostic=true template_unchanged=true")
    finally:
        temporary.cleanup()


if __name__ == "__main__":
    main()
