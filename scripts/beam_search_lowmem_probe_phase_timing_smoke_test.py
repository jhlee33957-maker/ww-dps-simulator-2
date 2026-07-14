from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TIMINGS = (
    "search_runtime_seconds",
    "accumulator_finalization_seconds",
    "checkpoint_manifest_generation_seconds",
    "result_creation_seconds",
    "cleanup_runtime_seconds",
    "total_process_runtime_seconds",
    "spill_write_seconds",
    "spill_sha_validation_seconds",
    "spill_restore_seconds",
    "duplicate_merge_seconds",
    "retained_selection_seconds",
    "pending_frontier_serialization_seconds",
    "route_store_compaction_seconds",
)


def main() -> int:
    env = dict(os.environ)
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    completed = subprocess.run(
        [sys.executable, "scripts/beam_search_lowmem_10000_probe_smoke_test.py"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=220,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    lines = [line for line in completed.stdout.splitlines() if line.startswith("LOWMEM_PROBE_METRICS=")]
    assert len(lines) == 1, completed.stdout
    metrics = json.loads(lines[0].split("=", 1)[1])
    for key in REQUIRED_TIMINGS:
        assert key in metrics
        assert float(metrics[key]) >= 0.0
    assert metrics["cleanup_completed"] is True
    assert metrics["spill_write_count"] > 0
    assert metrics["spill_restore_pass_count"] <= metrics["accumulator_finalization_count"]
    assert metrics["spill_restore_nodes_streamed"] <= 4096
    assert metrics["accumulator_finalization_count"] >= 1
    assert metrics["total_process_runtime_seconds"] < 220
    print("beam_search_lowmem_probe_phase_timing_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
