from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_search import BeamSearchRunner  # noqa: E402


def main() -> None:
    source = inspect.getsource(BeamSearchRunner._update_peak_metrics_for_node)
    for forbidden in ("json.dumps", "state_payload_size_bytes", "serialize_simulation_state", "node.to_json"):
        assert forbidden not in source, f"hot-path metric update must not perform full serialization: {forbidden}"
    with tempfile.TemporaryDirectory(prefix="beam-hot-path-") as output:
        result = _run(Path(output), max_expansions=120)
    assert result["expansions"] == 120
    assert result["metric_update_count"] >= result["payload_size_calculation_count"] + 1
    assert result["metric_update_count"] <= (result["payload_size_calculation_count"] * 3) + 1
    assert result["payload_size_calculation_count"] == result["expansions"]
    assert result["peak_serialized_payload_bytes"] < 65536
    assert result["peak_frontier_size"] == result["peak_live_nodes"]
    print("beam_search_hot_path_scalability_smoke_test ok")


def _run(output: Path, *, max_expansions: int) -> dict:
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
