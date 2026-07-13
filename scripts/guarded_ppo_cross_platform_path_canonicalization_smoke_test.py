from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import DEFAULT_PLAN_PATH, canonicalize_guarded_path

    examples = {
        "/mnt/data/review121/data/guarded_ppo_experiment_plan_v109.json": "data/guarded_ppo_experiment_plan_v109.json",
        "/mnt/data/fresh121/data/guarded_ppo_experiment_plan_v109.json": "data/guarded_ppo_experiment_plan_v109.json",
        "/mnt/data/review121/results/training_metadata.json": "results/training_metadata.json",
        "/tmp/extract/results/training_metadata.json": "results/training_metadata.json",
        "C:/Users/coree/OneDrive/Documents/GitHub/ww-dps-simulator-2/ww-dps-simulator-2/results/training_metadata.json": "results/training_metadata.json",
        r"C:\Users\coree\OneDrive\Documents\GitHub\ww-dps-simulator-2\ww-dps-simulator-2\results\training_metadata.json": "results/training_metadata.json",
        "data/guarded_ppo_experiment_plan_v109.json": "data/guarded_ppo_experiment_plan_v109.json",
    }
    for raw, expected in examples.items():
        actual = canonicalize_guarded_path(raw)
        assert actual == expected, f"{raw!r}: {actual!r} != {expected!r}"

    native_absolute = DEFAULT_PLAN_PATH.resolve()
    assert canonicalize_guarded_path(native_absolute) == "data/guarded_ppo_experiment_plan_v109.json"

    untrusted = "/outside/no/project/anchors/training_metadata.json"
    assert canonicalize_guarded_path(untrusted) == "training_metadata.json"
    print("guarded_ppo_cross_platform_path_canonicalization_smoke_test ok")


if __name__ == "__main__":
    main()
