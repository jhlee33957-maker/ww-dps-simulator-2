from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_plan import load_mcts_plan
from search.mcts_reporting import replay_completed_route
from search.mcts_search import MCTSSearch
from scripts.mcts_v117_test_utils import PLAN_PATH, compact_probe


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--json-output", type=Path, required=True)
    args = parser.parse_args(); plan = load_mcts_plan(PLAN_PATH); stage = dict(plan["stages"][0]); stage["maximum_simulations"] = 200
    started = time.perf_counter()
    first = MCTSSearch(plan=plan, stage=stage, output_root=args.output_root, max_simulations=100, allow_test_output_root=True).run()
    runner = MCTSSearch(plan=plan, stage=stage, output_root=args.output_root, max_simulations=200, allow_test_output_root=True)
    result = runner.run(resume=True); total_runtime = time.perf_counter() - started
    best = result["best_completed_route"]; replay = replay_completed_route(best)
    payload = {"compact": compact_probe(result, replay["resolved_sequence_sha256"]), "result": result,
               "probe_total_runtime_seconds": total_runtime, "checkpoint_resume": {"first": first["simulations_completed"], "resumed": result["simulations_completed"]},
               "slowdown_region_regression": {"seed": int(stage["seed"]), "through_simulation": 160,
                                               "simulation_160_completed": result["simulations_completed"] >= 160,
                                               "completed_normally_through_200": result["simulations_completed"] == 200}}
    args.json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))


if __name__ == "__main__": main()
