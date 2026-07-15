from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts.mcts_v118_probe_utils import run_three


def main() -> None:
    first, second = run_three(ROOT), run_three(ROOT)
    deterministic = ("logical_result_sha256", "rng_final_state_sha256", "mast_logical_sha256", "best_damage",
                     "completed_rollouts", "node_count")
    for left, right in zip(first, second, strict=True):
        assert left["seed"] == right["seed"] and all(left[key] == right[key] for key in deterministic)
    assert len({item["logical_result_sha256"] for item in first}) == 3
    print("mcts_v118_3x200_probe_repeatability_smoke_test ok " + json.dumps(first, sort_keys=True))


if __name__ == "__main__": main()
