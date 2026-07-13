from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_LIVE_NODE_BUDGET = 1024 * 9


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-frontier-bound-") as temp_dir:
        result = _run(Path(temp_dir))
    bounds = result["frontier_bounds"]
    assert result["stage_id"] == "calibration_30s"
    assert result["expansions"] == 2000
    assert bounds["pending_bucket_node_bound"] == 1024
    assert bounds["live_node_budget"] == CALIBRATION_LIVE_NODE_BUDGET
    assert bounds["all_pending_buckets_within_bound"] is True
    assert bounds["live_nodes_within_bound"] is True
    assert bounds["max_pending_bucket_node_count"] <= 1024
    assert result["live_node_count"] <= CALIBRATION_LIVE_NODE_BUDGET
    assert not (ROOT / "results" / "beam_search_v111").exists()
    print("beam_search_pending_frontier_bound_smoke_test ok")


def _run(output: Path) -> dict:
    command = [
        sys.executable,
        "search/run_beam_search.py",
        "--plan",
        "data/beam_search_plan_v111.json",
        "--execute",
        "--only-stage",
        "calibration_30s",
        "--output-root",
        str(output),
        "--max-expansions",
        "2000",
    ]
    result = subprocess.run(command, cwd=ROOT, env=_env(), text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    return json.loads(Path(summary["execution_result_path"]).read_text(encoding="utf-8"))


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    return env


if __name__ == "__main__":
    main()
