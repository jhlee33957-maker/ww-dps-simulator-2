from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-checkpoint-") as output:
        result = _run(Path(output), max_expansions=80)
    assert result["checkpoint_interval_expansions"] == 100000
    assert result["checkpoint_count"] == 2, result["checkpoint_count"]
    assert len(result["bucket_metrics"]) > result["checkpoint_count"]
    assert result["frontier_file_write_count"] < len(result["bucket_metrics"]) + 2
    assert result["frontier_file_write_count"] <= len(result["pending_buckets"]) + 1
    assert result["pending_buckets"]
    print("beam_search_checkpoint_interval_smoke_test ok")


def _run(output: Path, *, max_expansions: int) -> dict:
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
            str(max_expansions),
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
