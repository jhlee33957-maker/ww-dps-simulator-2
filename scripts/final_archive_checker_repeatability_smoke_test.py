from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT.parent / "ww-dps-simulator-2-112.zip"
PROTECTED_FILES = (
    "results/beam_search_v111/execution_result.json",
    "results/beam_search_v111/calibration_result_summary.json",
    "reports/beam_search_v111_calibration_results.md",
    "PROJECT_PROGRESS_STATE.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return env


def _terminate_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    else:
        process.kill()


def _assert_pid_gone(pid: int) -> None:
    if os.name == "nt":
        result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], check=False, text=True, capture_output=True, timeout=10)
        assert str(pid) not in result.stdout, result.stdout


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    assert args.runs >= 3
    archive = args.archive.resolve()
    assert archive.exists(), archive
    before_archive_hash = _sha256(archive)
    before_protected = {path: _sha256(ROOT / path) for path in PROTECTED_FILES}
    with zipfile.ZipFile(archive) as zf:
        assert not any("__pycache__" in name or name.endswith((".pyc", ".pyo")) for name in zf.namelist())

    timings: list[float] = []
    for run_index in range(1, args.runs + 1):
        command = [sys.executable, "scripts/manual_120s_bc_final_archive_integrity_smoke_test.py", "--archive", str(archive), "--orchestration-smoke"]
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        started = time.perf_counter()
        process = subprocess.Popen(command, cwd=ROOT, env=_environment(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
        try:
            stdout, stderr = process.communicate(timeout=args.timeout)
        except subprocess.TimeoutExpired as exc:
            _terminate_tree(process)
            stdout, stderr = process.communicate(timeout=10)
            raise AssertionError(f"repeatability run {run_index} timed out\n{stdout.decode(errors='replace')}\n{stderr.decode(errors='replace')}") from exc
        elapsed = time.perf_counter() - started
        assert process.returncode == 0, f"repeatability run {run_index} failed\n{stdout.decode(errors='replace')}\n{stderr.decode(errors='replace')}"
        assert b"manual_120s_bc_final_archive_integrity_smoke_test ok" in stdout
        _assert_pid_gone(process.pid)
        timings.append(elapsed)
        print(f"repeatability run {run_index} ok: {elapsed:.3f}s; surviving_descendants=0", flush=True)

    assert _sha256(archive) == before_archive_hash
    assert {path: _sha256(ROOT / path) for path in PROTECTED_FILES} == before_protected
    print(f"final_archive_checker_repeatability_smoke_test ok: timings={[round(value, 3) for value in timings]}")


if __name__ == "__main__":
    main()
