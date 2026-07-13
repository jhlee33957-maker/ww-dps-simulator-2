from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import build_future_commands, effective_seed, load_plan

    plan_path = ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"
    plan = load_plan(plan_path)
    expected = {
        "bc_conservative_seed_11": 11,
        "bc_exploratory_seed_73": 73,
        "scratch_control_seed_137": 137,
    }
    commands = build_future_commands(plan, plan_path=plan_path, output_root=ROOT)
    for branch in plan["branches"]:
        branch_id = branch["branch_id"]
        for chunk_index in (1, 2, 10):
            assert effective_seed(branch, chunk_index) == expected[branch_id] + chunk_index - 1
        first = next(item for item in commands if item.get("branch_id") == branch_id and item["chunk_index"] == 1)
        train = first["train"]
        assert train[train.index("--seed") + 1] == str(expected[branch_id])
        assert train[train.index("--branch-base-seed") + 1] == str(expected[branch_id])
        assert train[train.index("--effective-chunk-seed") + 1] == str(expected[branch_id])
    print("guarded_ppo_seed_contract_smoke_test ok")


if __name__ == "__main__":
    main()
