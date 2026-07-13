from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-resume-") as temp_dir:
        output = Path(temp_dir)
        first = _run(output, ["--execute", "--smoke-run", "--max-expansions", "5"])
        first_state = json.loads((output / "search_state.json").read_text(encoding="utf-8"))
        assert first["expansions"] == 5
        resumed = _run(output, ["--execute", "--smoke-run", "--resume", "--max-expansions", "10"])
        assert resumed["expansions"] >= first["expansions"]
        failed = subprocess.run(
            [sys.executable, "search/run_beam_search.py", "--execute", "--smoke-run", "--output-root", str(output), "--max-expansions", "10"],
            cwd=ROOT,
            env=_env(),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
        assert failed.returncode != 0
        current_state = json.loads((output / "search_state.json").read_text(encoding="utf-8"))
        frontier = Path(current_state["pending_buckets"][0]["path"])
        frontier.write_bytes(frontier.read_bytes() + b"corrupt")
        corrupt = subprocess.run(
            [sys.executable, "search/run_beam_search.py", "--execute", "--smoke-run", "--resume", "--output-root", str(output), "--max-expansions", "10"],
            cwd=ROOT,
            env=_env(),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
        assert corrupt.returncode != 0
    print("beam_search_resume_integrity_smoke_test ok")


def _run(output: Path, extra: list[str]) -> dict:
    result = subprocess.run(
        [sys.executable, "search/run_beam_search.py", "--plan", "data/beam_search_plan_v111.json", "--output-root", str(output), *extra],
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
