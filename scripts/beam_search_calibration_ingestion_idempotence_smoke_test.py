from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_FILES = (
    ROOT / "results" / "beam_search_v111" / "execution_result.json",
    ROOT / "results" / "beam_search_v111" / "calibration_result_summary.json",
    ROOT / "reports" / "beam_search_v111_calibration_results.md",
    ROOT / "PROJECT_PROGRESS_STATE.json",
)


def _hashes() -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in CANONICAL_FILES}


def _assert_canonical_text() -> None:
    for path in CANONICAL_FILES:
        data = path.read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf"), path
        assert b"\r" not in data, path
        assert data.endswith(b"\n"), path
        data.decode("utf-8")


def _run_ingestion() -> None:
    env = dict(os.environ)
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    result = subprocess.run([sys.executable, "scripts/ingest_beam_search_v111_calibration_results.py", "--write"], cwd=ROOT, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def main() -> None:
    before = _hashes()
    _assert_canonical_text()
    _run_ingestion()
    after_first = _hashes()
    assert after_first == before, (before, after_first)
    _run_ingestion()
    after_second = _hashes()
    assert after_second == before, (before, after_second)
    _assert_canonical_text()
    print("beam_search_calibration_ingestion_idempotence_smoke_test ok")


if __name__ == "__main__":
    main()
