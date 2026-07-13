from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import latest_branch_parent, load_plan, select_best_candidate

    plan_path = ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"
    plan = load_plan(plan_path)
    branch = plan["branches"][0]
    empty_state = {"chunks": []}
    assert latest_branch_parent(empty_state, branch) == ROOT / "models" / "maskable_ppo_bc_v105.zip"

    branch_10k = ROOT / "models" / "guarded_ppo_v109" / branch["branch_id"] / "step_000010000.zip"
    branch_20k = ROOT / "models" / "guarded_ppo_v109" / branch["branch_id"] / "step_000020000.zip"
    branch_state = {
        "chunks": [
            {
                "status": "completed",
                "branch_id": branch["branch_id"],
                "chunk_index": 1,
                "checkpoint_path": branch_10k.as_posix(),
                "total_damage": 4_000_000.0,
            }
        ]
    }
    assert latest_branch_parent(branch_state, branch) == branch_10k
    bc = {
        "kind": "verified_bc_model",
        "model_path": "models/maskable_ppo_bc_v105.zip",
        "externally_verified": True,
        "immutable_model": True,
        "total_damage": 5165134.682363356,
        "declared_order": 1,
    }
    best_after_10k = select_best_candidate([bc, branch_state["chunks"][0]])
    assert best_after_10k["kind"] == "verified_bc_model"
    branch_state["chunks"].append(
        {
            "status": "completed",
            "branch_id": branch["branch_id"],
            "chunk_index": 2,
            "checkpoint_path": branch_20k.as_posix(),
            "total_damage": 5_300_000.0,
            "externally_verified": False,
            "immutable_model": True,
            "declared_order": 101,
        }
    )
    assert latest_branch_parent(branch_state, branch) == branch_20k
    best_after_20k = select_best_candidate([bc, *branch_state["chunks"]])
    assert best_after_20k["checkpoint_path"] == branch_20k.as_posix()
    assert branch_state["chunks"][1]["checkpoint_path"] == branch_20k.as_posix()
    print("guarded_ppo_branch_continuation_smoke_test ok")


if __name__ == "__main__":
    main()
