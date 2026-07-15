from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from scripts.mcts_v117_test_utils import run_isolated_probe_worker


def main() -> None:
    root = Path(__file__).resolve().parents[1]; canonical = root / "results/mcts_v117_32gb/calibration_20k_seed_117001"
    assert not canonical.exists()
    with tempfile.TemporaryDirectory(prefix="mcts-real-200-") as tmp:
        temporary = Path(tmp); output = temporary / "run"; result_path = temporary / "result.json"
        payload, no_survivor = run_isolated_probe_worker(root=root, output=output, result_path=result_path)
        result = payload["result"]
        assert result["simulations_completed"] == 200 and result["completed_rollout_count"] >= 1
        assert result["normal_process_exit"] is True and result["termination_status"] == "simulation_budget_exhausted"
        assert payload["checkpoint_resume"] == {"first": 100, "resumed": 200}
        assert result["max_snapshot_reconstruction_replay_length"] <= 7
        assert payload["probe_total_runtime_seconds"] < 180.0
        assert no_survivor is True
        assert result["slowest_simulation_index"] is not None and result["slowest_simulation_index"] <= 200
        assert len(result["simulation_runtime_seconds"]) == 4
        assert result["lightweight_diagnostic_log_rows"] == 0
        assert result["lightweight_diagnostic_bytes"] == 0
        assert payload["slowdown_region_regression"] == {
            "seed": 117001, "through_simulation": 160,
            "simulation_160_completed": True, "completed_normally_through_200": True,
        }
        assert not list(temporary.rglob("*.pyc")) and not list(temporary.rglob("__pycache__"))
        metrics = {"runtime_seconds": payload["probe_total_runtime_seconds"], "simulations_per_second": 200 / payload["probe_total_runtime_seconds"],
                   "action_executions_per_second": result["total_action_executions"] / payload["probe_total_runtime_seconds"],
                   "completed_rollout_count": result["completed_rollout_count"], "best_completed_route": result["best_completed_route"],
                   "node_count": result["node_count"], "snapshot_metrics": result["snapshot_metrics"], "memory": result["memory"],
                   "simulation_runtime_seconds": result["simulation_runtime_seconds"],
                   "slowest_simulation_index": result["slowest_simulation_index"],
                   "slowest_simulation_selection_depth": result["slowest_simulation_selection_depth"],
                   "slowest_simulation_rollout_action_count": result["slowest_simulation_rollout_action_count"],
                   "maximum_individual_action_execution_seconds": result["maximum_individual_action_execution_seconds"],
                   "slowest_action_id": result["slowest_action_id"],
                   "slowest_action_active_character": result["slowest_action_active_character"],
                   "lightweight_diagnostic_log_rows": result["lightweight_diagnostic_log_rows"],
                   "lightweight_diagnostic_bytes": result["lightweight_diagnostic_bytes"],
                   "process_group_cleanup": "no_survivor",
                   "logical_result_sha256": result["logical_result_sha256"]}
        print(json.dumps(metrics, indent=2))
    assert not canonical.exists()
    print("mcts_200_probe_smoke_test ok")


if __name__ == "__main__": main()
