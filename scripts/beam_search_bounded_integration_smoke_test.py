from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTECTED = [
    "models/maskable_ppo_bc_v105.zip",
    "models/maskable_ppo_candidate_after_bc_v105.zip",
    "data/generated/manual_120s_bc_demonstration_v105.npz",
    "data/manual_120s_baseline_routes_v104.json",
    "results/guarded_ppo_v109/experiment_state.json",
]


def main() -> None:
    before = {path: _sha256(ROOT / path) for path in PROTECTED}
    canonical_before = _snapshot_canonical()
    with tempfile.TemporaryDirectory(prefix="beam-bounded-a-") as a, tempfile.TemporaryDirectory(prefix="beam-bounded-b-") as b:
        start = time.perf_counter()
        first = _run(Path(a))
        elapsed = time.perf_counter() - start
        second = _run(Path(b))
        assert first["stage_id"] == "smoke_3s"
        assert first["maximum_expansions"] <= 2000
        assert first["expansions"] <= 2000
        assert elapsed < 120.0
        assert first["best_partial_frontier_node"]["selected_sequence"] == second["best_partial_frontier_node"]["selected_sequence"]
        assert first["best_partial_frontier_node"]["future_fingerprint"] == second["best_partial_frontier_node"]["future_fingerprint"]
        resume = _run(Path(a), resume=True, max_expansions=first["expansions"] + 5)
        assert resume["expansions"] >= first["expansions"]
        assert resume["pending_bucket_indices"]
    assert before == {path: _sha256(ROOT / path) for path in PROTECTED}
    assert canonical_before == _snapshot_canonical()
    assert not (ROOT / "results" / "beam_search_v111").exists()
    print("beam_search_bounded_integration_smoke_test ok")


def _run(output: Path, *, resume: bool = False, max_expansions: int = 40) -> dict:
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
    if resume:
        args.insert(args.index("--output-root"), "--resume")
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


def _snapshot_canonical() -> dict[str, str]:
    root = ROOT / "results" / "beam_search_v111"
    if not root.exists():
        return {}
    return {path.relative_to(ROOT).as_posix(): _sha256(path) for path in root.rglob("*") if path.is_file()}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
