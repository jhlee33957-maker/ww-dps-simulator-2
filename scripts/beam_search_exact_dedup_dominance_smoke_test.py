from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_search import BeamSearchRunner, _smoke_stage
from search.beam_state import BeamNode


def main() -> None:
    stage = _smoke_stage(10)
    runner = BeamSearchRunner(plan={"party": "x", "initial_active_character": "x"}, stage=stage, plan_path=__import__("pathlib").Path("data/beam_search_plan_v111.json"), output_root=__import__("pathlib").Path("unused"))
    low = _node(1, 10.0, "same", "a")
    high = _node(2, 20.0, "same", "b")
    other = _node(3, 5.0, "other", "c")
    retained = runner._retain([low, high, other])
    assert high in retained
    assert low not in retained
    assert other in retained
    assert runner.deduplicated_states == 1
    print("beam_search_exact_dedup_dominance_smoke_test ok")


def _node(node_id: int, damage: float, fingerprint: str, diversity: str) -> BeamNode:
    return BeamNode(
        node_id=node_id,
        parent_id=None,
        selected_action_id=None,
        resolved_action_id=None,
        action_count=1,
        total_damage=damage,
        combat_time=0.0,
        current_time=0.0,
        state_payload={},
        future_fingerprint=fingerprint,
        diversity_key=diversity,
    )


if __name__ == "__main__":
    main()
