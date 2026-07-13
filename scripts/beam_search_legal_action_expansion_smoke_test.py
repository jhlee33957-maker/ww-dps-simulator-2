from __future__ import annotations

import tempfile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_search import BeamSearchRunner, _smoke_stage  # noqa: E402
from search.beam_plan import load_plan  # noqa: E402


def main() -> None:
    plan = load_plan()
    with tempfile.TemporaryDirectory(prefix="beam-legal-") as temp_dir:
        runner = BeamSearchRunner(plan=plan, stage=_smoke_stage(25), plan_path=ROOT / "data" / "beam_search_plan_v111.json", output_root=Path(temp_dir))
        sim = runner._create_simulation()
        expected = sim.valid_action_ids()
        result = runner.run(resume=False)
        first_bucket = result["bucket_metrics"][0]
        assert expected == [action for action in sim.get_policy_action_ids() if action in expected]
        assert result["expansions"] <= 25
        assert first_bucket["children"] == min(len(expected), 25)
        assert all(action in sim.get_policy_action_ids() for action in expected)
        assert "short_wait" in sim.get_policy_action_ids()
        route_store = result["route_store"]
        expanded_first_edges = [
            edge["selected_action_id"]
            for edge in route_store.values()
            if edge["parent_id"] == 0
        ]
        assert expanded_first_edges == expected[: len(expanded_first_edges)]
    print("beam_search_legal_action_expansion_smoke_test ok")


if __name__ == "__main__":
    main()
