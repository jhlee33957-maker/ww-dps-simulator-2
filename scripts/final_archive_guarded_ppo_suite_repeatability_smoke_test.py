from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.final_archive_checker_repeatability_smoke_test import (
    DEFAULT_ARCHIVE,
    PROTECTED_FILES,
    _assert_pid_gone,
    _environment,
    _sha256,
    _terminate_tree,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=60.0)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    assert args.runs >= 3
    archive = args.archive.resolve()
    assert archive.exists(), archive
    archive_before = _sha256(archive)
    protected_before = {path: _sha256(ROOT / path) for path in PROTECTED_FILES}
    timings: list[float] = []
    for run_index in range(1, args.runs + 1):
        started = time.perf_counter()
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        process = subprocess.Popen(
            [sys.executable, "scripts/final_archive_guarded_ppo_lightweight_suite.py"],
            cwd=ROOT,
            env=_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
        )
        try:
            stdout, stderr = process.communicate(timeout=args.timeout)
        except subprocess.TimeoutExpired as exc:
            _terminate_tree(process)
            stdout, stderr = process.communicate(timeout=10)
            raise AssertionError(f"guarded suite run {run_index} timed out\n{stdout.decode(errors='replace')}\n{stderr.decode(errors='replace')}") from exc
        elapsed = time.perf_counter() - started
        assert process.returncode == 0, f"guarded suite run {run_index} failed\n{stdout.decode(errors='replace')}\n{stderr.decode(errors='replace')}"
        assert b"final_archive_guarded_ppo_lightweight_suite ok" in stdout
        _assert_pid_gone(process.pid)
        timings.append(elapsed)
        print(f"guarded suite run {run_index} ok: {elapsed:.3f}s; surviving_descendants=0", flush=True)
    assert _sha256(archive) == archive_before
    assert {path: _sha256(ROOT / path) for path in PROTECTED_FILES} == protected_before
    print(f"final_archive_guarded_ppo_suite_repeatability_smoke_test ok: timings={[round(value, 3) for value in timings]}")


if __name__ == "__main__":
    main()
