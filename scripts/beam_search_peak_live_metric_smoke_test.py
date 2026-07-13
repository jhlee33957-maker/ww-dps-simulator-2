from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-peak-live-") as temp_dir:
        result = _run(Path(temp_dir))
    assert result["peak_live_nodes"] >= result["live_node_count"]
    assert result["frontier_bounds"]["peak_live_nodes_ge_live_node_count"] is True
    assert result["frontier_bounds"]["live_nodes_within_bound"] is True
    assert result["frontier_bounds"]["all_pending_buckets_within_bound"] is True
    print("beam_search_peak_live_metric_smoke_test ok")


def _run(output: Path) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            "search/run_beam_search.py",
            "--plan",
            "data/beam_search_plan_v111.json",
            "--execute",
            "--smoke-run",
            "--output-root",
            str(output),
            "--max-expansions",
            "2000",
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    return json.loads(Path(summary["execution_result_path"]).read_text(encoding="utf-8"))


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    return env


if __name__ == "__main__":
    main()
