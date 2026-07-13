from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_destination_bucket_test_utils import STAGE, make_node  # noqa: E402
from search.beam_search import DestinationBucketAccumulator  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-hot-path-") as temp_dir:
        accumulator = DestinationBucketAccumulator(
            bucket_index=4,
            stage=STAGE | {"destination_accumulator_unique_fingerprint_bound": 32},
            spill_root=Path(temp_dir),
            output_root=Path(temp_dir),
        )
        for index in range(250):
            accumulator.add(make_node(index + 1, damage=float(index), key=f"K{index % 17}"))
            assert accumulator.retained_set_finalization_count == 0
            assert accumulator.full_retained_set_scan_count == 0
        assert accumulator.spill_chunks
        assert accumulator.metrics()["retained_set_finalization_count"] == 1

    with tempfile.TemporaryDirectory(prefix="beam-hot-path-run-") as output_dir:
        command = [
            sys.executable,
            "search/run_beam_search.py",
            "--plan",
            "data/beam_search_plan_v111.json",
            "--execute",
            "--smoke-run",
            "--output-root",
            output_dir,
            "--max-expansions",
            "500",
        ]
        result = subprocess.run(command, cwd=ROOT, env=_env(), text=True, encoding="utf-8", capture_output=True, timeout=120)
        assert result.returncode == 0, result.stdout + result.stderr
        assert len(result.stdout.encode("utf-8")) < 4096
        summary = json.loads(result.stdout)
        payload = json.loads(Path(summary["execution_result_path"]).read_text(encoding="utf-8"))
        assert payload["accumulator_finalization_count"] < payload["expansions"]
        assert payload["payload_size_calculation_count"] == payload["expansions"]
    print("beam_search_destination_accumulator_hot_path_smoke_test ok")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    return env


if __name__ == "__main__":
    main()
