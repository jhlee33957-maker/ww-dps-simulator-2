from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-route-store-") as output:
        result = _run(Path(output), max_expansions=180)
    assert result["route_store_entry_count"] < result["next_node_id"], (result["route_store_entry_count"], result["next_node_id"])
    assert result["route_store_entry_count"] <= result["peak_live_nodes"] + 256
    for edge in result["route_store"].values():
        assert set(edge) <= {"node_id", "parent_id", "selected_action_id", "resolved_action_id"}
    for route in result["completed_routes"]:
        assert "state_payload" not in route
        assert "selected_sequence" in route
        assert "resolved_sequence" in route
    print("beam_search_route_store_compaction_smoke_test ok")


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
