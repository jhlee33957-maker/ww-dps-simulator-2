from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_search import BeamSearchRunner
from scripts.beam_search_exact_dedup_dominance_smoke_test import _node


def main() -> None:
    stage = {
        "stage_id": "toy",
        "time_bucket_width": 1.0,
        "beam_width": 2,
        "global_damage_quota": 1,
        "diversity_retention_quota": 1,
        "max_states_per_diversity_key": 1,
        "maximum_expansions": 10,
        "combat_duration": 2.0,
    }
    runner = BeamSearchRunner(plan={"party": "toy", "initial_active_character": "toy"}, stage=stage, plan_path=__import__("pathlib").Path("data/beam_search_plan_v111.json"), output_root=__import__("pathlib").Path("unused"))
    greedy = _node(1, 100.0, "greedy", "damage_now")
    setup = _node(2, 1.0, "setup", "delayed_setup")
    retained = runner._retain([greedy, setup])
    assert retained == [greedy, setup]
    terminal = {"greedy": 100.0, "setup": 500.0}
    assert terminal[setup.future_fingerprint] > terminal[greedy.future_fingerprint]
    print("beam_search_delayed_payoff_diversity_smoke_test ok")


if __name__ == "__main__":
    main()
