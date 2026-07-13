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
    with tempfile.TemporaryDirectory(prefix="beam-acc-manifest-") as temp_dir:
        root = Path(temp_dir)
        accumulator = DestinationBucketAccumulator(
            bucket_index=2,
            stage=STAGE | {"destination_accumulator_unique_fingerprint_bound": 64},
            spill_root=root,
            output_root=root,
        )
        for index in range(1500):
            accumulator.add(make_node(index + 1, damage=float(index), key=f"K{index % 37}"))
        manifest = accumulator.manifest(force_spill=True, retained_view_count=1024)
        manifest_size = len(json.dumps(manifest, separators=(",", ":")).encode("utf-8"))
        assert manifest_size < 200_000
        assert "nodes" not in manifest
        assert sum(Path(chunk["path"]).stat().st_size for chunk in manifest["spill_chunks"]) > 0

    with tempfile.TemporaryDirectory(prefix="beam-manifest-run-") as output_dir:
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
            "1000",
        ]
        result = subprocess.run(command, cwd=ROOT, env=_env(), text=True, encoding="utf-8", capture_output=True, timeout=180)
        assert result.returncode == 0, result.stdout + result.stderr
        assert len(result.stdout.encode("utf-8")) < 4096
        state_path = Path(json.loads(result.stdout)["search_state_path"])
        assert state_path.stat().st_size < 5_000_000
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert all("nodes" not in payload for payload in state["destination_bucket_accumulators"].values())
    print("beam_search_destination_accumulator_manifest_size_smoke_test ok")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    return env


if __name__ == "__main__":
    main()
