from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_search import BeamSearchRunner  # noqa: E402
from search.beam_state import BeamNode  # noqa: E402


def main() -> None:
    plan = {
        "candidate": "111",
        "party": "aemeath_mornye_lynae_enabled_test_party",
        "initial_active_character": "aemeath",
        "completed_route_leaderboard_size": 128,
    }
    stage = {"stage_id": "unit", "combat_duration": 3.0, "maximum_expansions": 1, "time_bucket_width": 0.5, "beam_width": 1}
    runner = BeamSearchRunner(plan=plan, stage=stage, plan_path=ROOT / "data" / "beam_search_plan_v111.json", output_root=ROOT)
    runner.route_store[0] = {"node_id": 0, "parent_id": None, "selected_action_id": None, "resolved_action_id": None}
    for index in range(140):
        node_id = index + 1
        action_id = f"unit_action_{index:03d}"
        runner.route_store[node_id] = {"node_id": node_id, "parent_id": 0, "selected_action_id": action_id, "resolved_action_id": action_id}
        runner._record_completed(
            BeamNode(
                node_id=node_id,
                parent_id=0,
                selected_action_id=action_id,
                resolved_action_id=action_id,
                action_count=1,
                total_damage=1000.0,
                combat_time=3.0,
                current_time=3.0,
                state_payload={},
                future_fingerprint=f"fp-{index}",
                diversity_key="unit",
                complete=True,
            )
        )
    orders = [route["completion_order"] for route in runner.completed]
    assert len(orders) == runner.completed_leaderboard_size
    assert len(set(orders)) == len(orders)
    assert min(orders) == 1
    assert runner.next_completion_order == 141
    assert runner.best_completed_search_route["completion_order"] == 1
    print("beam_search_completion_order_smoke_test ok")


if __name__ == "__main__":
    main()
