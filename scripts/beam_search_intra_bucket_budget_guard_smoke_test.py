from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    uninterrupted_500 = _run_temp(500)
    wall_first, wall_resumed = _interrupted_then_resumed(500, "--wall-clock-limit-seconds", "0.001")
    assert wall_first["status"] == "wall_clock_budget_exhausted"
    _assert_equivalent(uninterrupted_500, wall_resumed)
    uninterrupted_2000 = _run_temp(2000)
    memory_first, memory_resumed = _interrupted_then_resumed(2000, "--memory-budget-bytes", "2000000")
    assert memory_first["status"] == "memory_budget_exhausted"
    assert memory_first["partial_action_cursors"] or memory_first["bucket_resume_queues"] or memory_first["pending_buckets"]
    _assert_equivalent(uninterrupted_2000, memory_resumed)
    print("beam_search_intra_bucket_budget_guard_smoke_test ok")


def _assert_equivalent(left: dict, right: dict) -> None:
    for key in (
        "best_completed_search_route",
        "best_partial_frontier_node",
        "completed_routes",
        "expansions",
        "next_node_id",
        "next_completion_order",
        "pending_bucket_indices",
        "partial_action_cursors",
        "bucket_resume_queues",
        "live_node_count",
        "frontier_bounds",
    ):
        assert left.get(key) == right.get(key), key


def _interrupted_then_resumed(max_expansions: int, limit_arg: str, limit_value: str) -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory(prefix="beam-budget-resume-") as temp_dir:
        output = Path(temp_dir)
        first = _run(output, max_expansions, extra_args=[limit_arg, limit_value])
        resumed = _run(output, max_expansions, resume=True)
        return first, resumed


def _run_temp(max_expansions: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="beam-budget-uninterrupted-") as temp_dir:
        return _run(Path(temp_dir), max_expansions)


def _run(output: Path, max_expansions: int, *, resume: bool = False, extra_args: list[str] | None = None) -> dict:
    command = [
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
        command.insert(command.index("--output-root"), "--resume")
    if extra_args:
        command.extend(extra_args)
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
