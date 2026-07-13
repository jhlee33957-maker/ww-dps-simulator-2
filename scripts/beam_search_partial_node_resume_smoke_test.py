from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-partial-a-") as uninterrupted_dir, tempfile.TemporaryDirectory(prefix="beam-partial-b-") as resumed_dir:
        first = _run(Path(resumed_dir), max_expansions=1)
        assert first["partial_action_cursors"] == {"0": 1}, first["partial_action_cursors"]
        resumed = _run(Path(resumed_dir), max_expansions=25, resume=True)
        uninterrupted = _run(Path(uninterrupted_dir), max_expansions=25)
    assert resumed["expansions"] == uninterrupted["expansions"] == 25
    assert resumed["best_partial_frontier_node"]["selected_sequence"] == uninterrupted["best_partial_frontier_node"]["selected_sequence"]
    assert resumed["pending_bucket_indices"] == uninterrupted["pending_bucket_indices"]
    assert resumed["completed_routes"] == uninterrupted["completed_routes"]
    print("beam_search_partial_node_resume_smoke_test ok")


def _run(output: Path, *, max_expansions: int, resume: bool = False) -> dict:
    args = [
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
    ]
    if resume:
        args.insert(args.index("--output-root"), "--resume")
    result = subprocess.run(
        args,
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
