from __future__ import annotations

import json
import sys
import time
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from scripts.mcts_v117_test_utils import run_isolated_probe_worker


def run(root: Path, base: Path, label: str) -> dict:
    output = base / label; result_path = base / f"{label}.json"
    payload, no_survivor = run_isolated_probe_worker(root=root, output=output, result_path=result_path)
    assert no_survivor is True
    return payload


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="mcts-repeat-200-") as tmp:
        base = Path(tmp); first = run(root, base, "a"); second = run(root, base, "b")
        assert first["compact"] == second["compact"]
        assert first["result"]["normal_process_exit"] is second["result"]["normal_process_exit"] is True
    elapsed = time.perf_counter() - started
    assert elapsed < 240.0
    print(json.dumps({**first["compact"], "two_run_runtime_seconds": elapsed,
                      "process_group_cleanup": "no_survivors"}, indent=2))
    print("mcts_200_probe_repeatability_smoke_test ok")


if __name__ == "__main__": main()
