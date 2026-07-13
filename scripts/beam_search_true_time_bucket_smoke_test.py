from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-bucket-a-") as a, tempfile.TemporaryDirectory(prefix="beam-bucket-b-") as b:
        first = _run(Path(a))
        second = _run(Path(b))
    metrics = first["bucket_metrics"]
    assert [item["bucket_index"] for item in metrics[:2]] == [0, 0], metrics
    assert first["pending_bucket_indices"] == [0, 1, 2, 3], first["pending_bucket_indices"]
    assert first["peak_frontier_size"] >= 1
    assert first["zero_time_expansion_count"] > 0
    assert first["best_partial_frontier_node"]["selected_sequence"] == second["best_partial_frontier_node"]["selected_sequence"]
    assert first["best_partial_frontier_node"]["future_fingerprint"] == second["best_partial_frontier_node"]["future_fingerprint"]
    assert all(item["bucket_index"] <= first["pending_bucket_indices"][-1] for item in metrics)
    print("beam_search_true_time_bucket_smoke_test ok")


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
            "20",
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
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
