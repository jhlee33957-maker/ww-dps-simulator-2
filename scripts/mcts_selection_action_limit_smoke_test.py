from __future__ import annotations

from mcts_selection_guard_test_support import runner_with_chain
from search.search_state_codec import full_node_state_fingerprint


def main() -> None:
    runner, temporary = runner_with_chain(512, zero_time=False)
    try:
        before_nodes = runner.tree.node_count
        template_fp = full_node_state_fingerprint(runner.template)
        runner._simulate_once()
        assert runner.tree.node_count == before_nodes == 513
        assert int(runner.tree.depth[: runner.tree.node_count].max()) == 512
        assert runner.invalid_rollout_counts == {"maximum_actions_exceeded_before_expansion": 1}
        assert full_node_state_fingerprint(runner.template) == template_fp
        print("mcts_selection_action_limit_smoke_test ok max_depth=512 no_depth_513=true")
    finally:
        temporary.cleanup()


if __name__ == "__main__":
    main()
