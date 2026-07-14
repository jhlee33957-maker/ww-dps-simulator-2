from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-uninterrupted-") as uninterrupted_dir, tempfile.TemporaryDirectory(prefix="beam-resumed-") as resumed_dir:
        uninterrupted = _run(Path(uninterrupted_dir), 2000)
        first = _run(Path(resumed_dir), 1000)
        assert first["pending_buckets"]
        resumed = _run(Path(resumed_dir), 2000, resume=True)
        uninterrupted_pending = _pending_node_payloads(uninterrupted)
        resumed_pending = _pending_node_payloads(resumed)
    _assert_equivalent(uninterrupted, resumed)
    assert uninterrupted_pending == resumed_pending
    assert _logical_accumulator_contract(uninterrupted) == _logical_accumulator_contract(resumed)
    assert resumed["expansions"] == uninterrupted["expansions"] == 2000
    assert resumed["status"] == uninterrupted["status"] == "expansion_budget_exhausted"
    print("beam_search_resume_equivalence_smoke_test ok")


def _assert_equivalent(uninterrupted: dict, resumed: dict) -> None:
    exact_keys = [
        "best_completed_search_route",
        "best_partial_frontier_node",
        "completed_routes",
        "expansions",
        "next_node_id",
        "next_completion_order",
        "deduplicated_states",
        "pruned_states",
        "zero_time_expansion_count",
        "pending_bucket_indices",
        "completed_buckets",
        "partial_action_cursors",
        "bucket_resume_queues",
        "live_node_count",
        "termination_status",
    ]
    for key in exact_keys:
        assert uninterrupted.get(key) == resumed.get(key), key


def _logical_accumulator_contract(result: dict) -> dict[str, dict[str, int]]:
    # A forced checkpoint may split the same candidate stream into additional
    # physical spill chunks. Compare the exact logical counts, not chunk layout
    # or orphan lineage retained solely for those equivalent spill records.
    return {
        key: {
            "candidates_seen": int(value["candidates_seen"]),
            "retained_view_count": int(value["retained_view_count"]),
            "bucket_index": int(value["bucket_index"]),
        }
        for key, value in result["destination_bucket_accumulators"].items()
    }
def _pending_node_payloads(result: dict) -> dict[int, list[dict]]:
    payloads: dict[int, list[dict]] = {}
    for entry in result["pending_buckets"]:
        import gzip

        with gzip.open(Path(entry["path"]), "rb") as file:
            payloads[int(entry["bucket_index"])] = json.loads(file.read().decode("utf-8"))["nodes"]
    return payloads


def _run(output: Path, max_expansions: int, *, resume: bool = False) -> dict:
    args = [
        sys.executable,
        "search/run_beam_search.py",
        "--plan",
        "data/beam_search_plan_v114_32gb.json",
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


if __name__ == "__main__":
    main()
