from __future__ import annotations
import copy
import tempfile
import time
from pathlib import Path
from typing import Any

from search.mcts_plan import load_mcts_plan
from search.mcts_search import MCTSSearch


def run_three(root: Path) -> list[dict[str, Any]]:
    plan = load_mcts_plan(root / "data/mcts_plan_v118_32gb_3x50k.json")
    results = []
    with tempfile.TemporaryDirectory(prefix="mcts-v118-3x200-") as tmp:
        temporary = Path(tmp)
        for original in plan["stages"]:
            stage = copy.deepcopy(original)
            stage.update(maximum_simulations=200, maximum_nodes=202, combat_duration=4.0,
                         checkpoint_interval_simulations=100, limit_check_interval_simulations=16,
                         wall_clock_budget_seconds=600, canonical_output_root="temporary_probe_only")
            output = temporary / str(stage["seed"]); started = time.perf_counter()
            result = MCTSSearch(plan=plan, stage=stage, output_root=output, allow_test_output_root=True).run()
            results.append({"seed": stage["seed"], "simulations": result["simulations_completed"],
                            "logical_result_sha256": result["logical_result_sha256"],
                            "rng_final_state_sha256": result["rng_final_state_sha256"],
                            "mast_logical_sha256": result["mast_logical_sha256"],
                            "best_damage": result["best_completed_route"]["total_damage"],
                            "completed_rollouts": result["completed_rollout_count"],
                            "node_count": result["node_count"], "peak_rss_bytes": result["memory"]["process_peak_rss_bytes"],
                            "conservative_memory_bytes": result["memory"]["conservative_total_estimate_bytes"],
                            "runtime_seconds": time.perf_counter() - started,
                            "normal_process_exit": result["normal_process_exit"]})
    return results
