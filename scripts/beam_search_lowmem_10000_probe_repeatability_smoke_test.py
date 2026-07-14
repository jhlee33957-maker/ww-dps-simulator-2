from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_lowmem_10000_probe_smoke_test import tree_digest


TIMEOUT_SECONDS = 220
DETERMINISTIC_KEYS = (
    "expansions",
    "peak_live_nodes",
    "peak_tracked_memory_bytes",
    "spill_chunk_count",
    "accumulator_spill_bytes",
    "accumulator_directory_bytes",
    "maximum_spill_chunk_uncompressed_bytes",
    "maximum_spill_serialization_buffer_bytes",
    "maximum_spill_restore_buffer_bytes",
    "maximum_finalization_unique_set_bytes",
    "maximum_final_sort_list_bytes",
    "checkpoint_count",
    "spill_write_count",
    "spill_sha_validation_count",
    "spill_restore_pass_count",
    "spill_restore_nodes_streamed",
    "accumulator_finalization_count",
    "checkpoint_manifest_generation_count",
    "forced_checkpoint_manifest_generation_count",
    "best_partial_future_fingerprint",
    "best_partial_total_damage",
    "deterministic_result_sha256",
)


def _cache_paths() -> list[str]:
    paths = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if ".venv" in relative.parts or ".git" in relative.parts:
            continue
        if path.is_file() and (path.suffix in {".pyc", ".pyo"} or "__pycache__" in relative.parts or ".pytest_cache" in relative.parts):
            paths.append(relative.as_posix())
    return sorted(paths)


def _run_once() -> dict[str, Any]:
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
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    started = time.perf_counter()
    process = subprocess.Popen(
        [sys.executable, "scripts/beam_search_lowmem_10000_probe_smoke_test.py"],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=os.name != "nt",
        creationflags=creationflags,
    )
    try:
        stdout, stderr = process.communicate(timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise AssertionError(f"10k probe exceeded {TIMEOUT_SECONDS}s")
    elapsed = time.perf_counter() - started
    assert process.returncode == 0, stdout + stderr
    assert process.poll() is not None
    metrics_lines = [line for line in stdout.splitlines() if line.startswith("LOWMEM_PROBE_METRICS=")]
    assert len(metrics_lines) == 1, stdout
    assert "beam_search_lowmem_10000_probe_smoke_test: PASS" in stdout
    metrics = json.loads(metrics_lines[0].split("=", 1)[1])
    assert elapsed < TIMEOUT_SECONDS
    return {"wall_runtime_seconds": elapsed, "metrics": metrics}


def main() -> int:
    canonical = ROOT / "results/beam_search_v113_lowmem_32gb"
    canonical_before = tree_digest(canonical)
    caches_before = _cache_paths()
    first = _run_once()
    second = _run_once()
    first_deterministic = {key: first["metrics"][key] for key in DETERMINISTIC_KEYS}
    second_deterministic = {key: second["metrics"][key] for key in DETERMINISTIC_KEYS}
    if first_deterministic != second_deterministic:
        differences = {
            key: {"run_1": first_deterministic[key], "run_2": second_deterministic[key]}
            for key in DETERMINISTIC_KEYS
            if first_deterministic[key] != second_deterministic[key]
        }
        raise AssertionError("Deterministic probe metric mismatch: " + json.dumps(differences, sort_keys=True))
    assert tree_digest(canonical) == canonical_before
    assert _cache_paths() == caches_before
    print(json.dumps({"run_1": first, "run_2": second}, indent=2, sort_keys=True), flush=True)
    print("beam_search_lowmem_10000_probe_repeatability_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
