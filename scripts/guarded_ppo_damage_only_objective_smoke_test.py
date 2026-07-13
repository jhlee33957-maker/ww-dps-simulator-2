from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import select_best_candidate

    candidates = [
        {"branch_id": "a", "total_damage": 100.0, "route_similarity": 1.0},
        {"branch_id": "b", "total_damage": 101.0, "route_similarity": 0.0},
        {"branch_id": "c", "total_damage": 100.5, "character_balance_score": 999.0},
    ]
    assert select_best_candidate(candidates)["branch_id"] == "b"
    tied = [
        {"branch_id": "first", "total_damage": 200.0, "externally_verified": False, "immutable_model": True},
        {"branch_id": "verified", "total_damage": 200.0, "externally_verified": True, "immutable_model": True},
    ]
    assert select_best_candidate(tied)["branch_id"] == "verified"
    near_tie = [
        {"branch_id": "verified_bc", "total_damage": 1000.0, "externally_verified": True, "immutable_model": True, "declared_order": 1},
        {"branch_id": "tiny_noise", "total_damage": 1000.0 + 5e-7, "externally_verified": False, "immutable_model": True, "declared_order": 2},
    ]
    assert select_best_candidate(near_tie)["branch_id"] == "verified_bc"
    strictly_better = [
        {"branch_id": "verified_bc", "total_damage": 1000.0, "externally_verified": True, "immutable_model": True, "declared_order": 1},
        {"branch_id": "branch", "total_damage": 1000.0 + 2e-6, "externally_verified": False, "immutable_model": True, "declared_order": 2},
    ]
    assert select_best_candidate(strictly_better)["branch_id"] == "branch"
    print("guarded_ppo_damage_only_objective_smoke_test ok")


if __name__ == "__main__":
    main()
