from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    assert _run([]).returncode != 0
    assert _run(["--resume"]).returncode != 0
    assert _run(["--execute", "--only-stage", "missing"]).returncode != 0
    assert _run(["--execute", "--max-expansions", "0"]).returncode != 0
    dry = _run(["--plan", "data/beam_search_plan_v111.json", "--dry-run-plan"])
    assert dry.returncode == 0
    assert "beam_search_dry_run_plan_ok" in dry.stdout
    assert not (ROOT / "results" / "beam_search_v111").exists()
    with tempfile.TemporaryDirectory(prefix="beam-cli-") as temp_dir:
        smoke = _run(["--plan", "data/beam_search_plan_v111.json", "--execute", "--smoke-run", "--output-root", temp_dir, "--max-expansions", "3"])
        assert smoke.returncode == 0
    print("beam_search_cli_execution_gate_smoke_test ok")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "search/run_beam_search.py", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )


if __name__ == "__main__":
    main()
