from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_lowmem_10000_probe_smoke_test import tree_digest
from search.beam_plan import LOWMEM_32GB_PLAN_PATH


TIMEOUT_SECONDS = 220
HISTORICAL_SUMMARY = ROOT / "results/beam_search_v114_lowmem_10000_probe_summary.json"
EXPECTED_HISTORICAL_SUMMARY_SHA256 = "61e789992660dd49e9183c7f4e7306ceafb52d7eff5a2ee79ac24292bb78ecff"
EXPECTED_HASH_GUARD_CHECKPOINTS = ("before_runs", "after_run_1", "after_run_2", "after_both")
DETERMINISTIC_KEYS = (
    "plan_path",
    "plan_sha256",
    "stage_id",
    "resolved_accumulator_spill_format",
    "accumulator_spill_chunk_schema",
    "expansions",
    "peak_live_nodes",
    "peak_tracked_memory_bytes",
    "spill_chunk_count",
    "spill_chunk_sha256s",
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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _assert_historical_summary_hash(path: Path = HISTORICAL_SUMMARY) -> str:
    assert path.is_file(), f"Protected historical summary is missing: {path}"
    actual = _file_sha256(path)
    assert actual == EXPECTED_HISTORICAL_SUMMARY_SHA256, actual
    return actual


def _results_state() -> tuple[str | None, str]:
    results_root = ROOT / "results"
    metadata = hashlib.sha256()
    for path in sorted(item for item in results_root.rglob("*") if item.is_file()):
        stat = path.stat()
        metadata.update(path.relative_to(results_root).as_posix().encode("utf-8"))
        metadata.update(f":{stat.st_size}:{stat.st_mtime_ns}".encode("ascii"))
    return tree_digest(results_root), metadata.hexdigest()


def _assert_results_unchanged(before: tuple[str | None, str], after: tuple[str | None, str]) -> None:
    assert after == before, "Default probe execution modified a file under results/"


def _assert_hash_guard_checkpoints(checkpoints: list[str]) -> None:
    assert tuple(checkpoints) == EXPECTED_HASH_GUARD_CHECKPOINTS


def _expect_rejection(callback) -> None:
    try:
        callback()
    except AssertionError:
        return
    raise AssertionError("Required mutation was not rejected")


def _assert_mutation_guards() -> int:
    canonical_bytes = HISTORICAL_SUMMARY.read_bytes()
    with tempfile.TemporaryDirectory(prefix="beam-probe-history-mutations-") as temporary:
        root = Path(temporary)
        mutated = root / "mutated.json"
        changed = bytearray(canonical_bytes)
        changed[0] ^= 1
        mutated.write_bytes(changed)
        _expect_rejection(lambda: _assert_historical_summary_hash(mutated))
        _expect_rejection(lambda: _assert_historical_summary_hash(root / "deleted.json"))
    _expect_rejection(lambda: _assert_results_unchanged(("before", "before"), ("after", "after")))
    _expect_rejection(lambda: _assert_hash_guard_checkpoints(list(EXPECTED_HASH_GUARD_CHECKPOINTS[:-1])))
    return 4


def _cache_paths() -> list[str]:
    paths = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if ".venv" in relative.parts or ".git" in relative.parts:
            continue
        if path.is_file() and (path.suffix in {".pyc", ".pyo"} or "__pycache__" in relative.parts or ".pytest_cache" in relative.parts):
            paths.append(relative.as_posix())
    return sorted(paths)


def _run_once(plan_path: Path, summary_output: Path) -> dict[str, Any]:
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
        [
            sys.executable,
            "scripts/beam_search_lowmem_10000_probe_smoke_test.py",
            "--plan",
            plan_path.relative_to(ROOT).as_posix(),
            "--summary-output",
            str(summary_output),
        ],
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
    diagnostic_summary = json.loads(summary_output.read_text(encoding="utf-8"))
    assert diagnostic_summary["schema_version"] == "beam_search_lowmem_10000_probe_diagnostic"
    assert all(diagnostic_summary[key] == value for key, value in metrics.items())
    assert metrics["normal_process_exit"] is True
    assert metrics["cleanup_completed"] is True
    assert metrics["canonical_output_mutated"] is False
    assert elapsed < TIMEOUT_SECONDS
    return {"wall_runtime_seconds": elapsed, "metrics": metrics, "diagnostic_summary": diagnostic_summary}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=LOWMEM_32GB_PLAN_PATH)
    args = parser.parse_args(argv)
    plan_path = args.plan if args.plan.is_absolute() else ROOT / args.plan
    protected_roots = (
        ROOT / "results/beam_search_v113_lowmem_32gb",
        ROOT / "results/beam_search_v114_lowmem_32gb",
    )
    protected_before = {path: tree_digest(path) for path in protected_roots}
    caches_before = _cache_paths()
    hash_guard_checkpoints: list[str] = []
    _assert_historical_summary_hash()
    hash_guard_checkpoints.append("before_runs")
    results_before = _results_state()
    with tempfile.TemporaryDirectory(prefix="beam-lowmem-10000-repeatability-") as temporary:
        diagnostic_root = Path(temporary)
        first = _run_once(plan_path, diagnostic_root / "run_1.json")
        _assert_historical_summary_hash()
        hash_guard_checkpoints.append("after_run_1")
        _assert_results_unchanged(results_before, _results_state())
        second = _run_once(plan_path, diagnostic_root / "run_2.json")
        _assert_historical_summary_hash()
        hash_guard_checkpoints.append("after_run_2")
        _assert_results_unchanged(results_before, _results_state())
    first_deterministic = {key: first["metrics"][key] for key in DETERMINISTIC_KEYS}
    second_deterministic = {key: second["metrics"][key] for key in DETERMINISTIC_KEYS}
    if first_deterministic != second_deterministic:
        differences = {
            key: {"run_1": first_deterministic[key], "run_2": second_deterministic[key]}
            for key in DETERMINISTIC_KEYS
            if first_deterministic[key] != second_deterministic[key]
        }
        raise AssertionError("Deterministic probe metric mismatch: " + json.dumps(differences, sort_keys=True))
    assert first["metrics"]["spill_chunk_sha256s"] == second["metrics"]["spill_chunk_sha256s"]
    assert first["metrics"]["best_partial_future_fingerprint"] == second["metrics"]["best_partial_future_fingerprint"]
    assert first["metrics"]["best_partial_total_damage"] == second["metrics"]["best_partial_total_damage"]
    for path, digest in protected_before.items():
        assert tree_digest(path) == digest
    _assert_historical_summary_hash()
    hash_guard_checkpoints.append("after_both")
    _assert_hash_guard_checkpoints(hash_guard_checkpoints)
    mutations_rejected = _assert_mutation_guards()
    assert _cache_paths() == caches_before
    print(json.dumps({"run_1": first, "run_2": second}, indent=2, sort_keys=True), flush=True)
    print(
        "beam_search_lowmem_10000_probe_repeatability_smoke_test: PASS "
        f"historical_sha256={EXPECTED_HISTORICAL_SUMMARY_SHA256} mutations_rejected={mutations_rejected}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
