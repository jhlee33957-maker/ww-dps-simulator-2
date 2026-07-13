from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-cli-compact-") as output_dir:
        result = subprocess.run(
            [
                sys.executable,
                "search/run_beam_search.py",
                "--plan",
                "data/beam_search_plan_v111.json",
                "--execute",
                "--smoke-run",
                "--output-root",
                output_dir,
                "--max-expansions",
                "250",
            ],
            cwd=ROOT,
            env=_env(),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert len(result.stdout.encode("utf-8")) < 4096
        summary = json.loads(result.stdout)
        assert summary["schema_version"] == "beam_search_compact_cli_summary_v111"
        assert summary["compact_output"] is True
        assert "route_store" not in summary
        assert Path(summary["search_state_path"]).exists()
        assert Path(summary["execution_result_path"]).exists()
    print("beam_search_compact_cli_output_smoke_test ok")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    return env


if __name__ == "__main__":
    main()
