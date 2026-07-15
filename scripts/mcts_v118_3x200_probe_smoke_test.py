from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from search.mcts_plan import load_mcts_plan
from scripts.mcts_v118_probe_utils import run_three


def main() -> None:
    plan = load_mcts_plan(ROOT / "data/mcts_plan_v118_32gb_3x50k.json")
    results = run_three(ROOT)
    assert [item["seed"] for item in results] == [118001, 118002, 118003]
    assert all(item["simulations"] == item["completed_rollouts"] == 200 and item["node_count"] == 201
               and item["normal_process_exit"] for item in results)
    assert len({item["logical_result_sha256"] for item in results}) == 3
    assert all(not (ROOT / stage["canonical_output_root"]).exists() for stage in plan["stages"])
    assert not plan["calibration_result_guidance"] and not plan["beam_route_guidance"] and not plan["bc_ppo_policy_guidance"]
    print("mcts_v118_3x200_probe_smoke_test ok " + json.dumps(results, sort_keys=True))


if __name__ == "__main__": main()
