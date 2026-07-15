from __future__ import annotations
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from search.mcts_plan import load_mcts_plan, validate_mcts_plan


def main() -> None:
    path = ROOT / "data/mcts_plan_v118_32gb_3x50k.json"
    plan = load_mcts_plan(path)
    assert len(plan["stages"]) == 3 and plan["execution_contract"]["explicit_only_stage_required"]
    for index, stage in enumerate(plan["stages"], 1):
        seed = 118000 + index
        assert stage["stage_id"] == f"production_50k_seed_{seed}" and stage["seed"] == seed
        assert stage["initial_tree"] == stage["initial_mast"] == "empty" and not stage["import_prior_route"]
        assert stage["checkpoint_retention_generations"] == 2 and stage["allow_corrupt_latest_fallback"]
    mutations = [
        ("stages.0.seed", 9), ("stages", plan["stages"][:2]), ("stages.1.stage_id", "bad"),
        ("stages.2.canonical_output_root", "bad"), ("stages.0.maximum_simulations", 49999),
        ("stages.0.maximum_nodes", 60000), ("uct.exploration_constant", 1.0),
        ("reward.terminal_scale", 1.0), ("progressive_widening.coefficient", 3.0),
        ("mast.epsilon", 0.1), ("stages.0.memory_budget_bytes", 1),
        ("calibration_result_guidance", True), ("prior_mcts_tree_guidance", True),
        ("prior_mcts_mast_guidance", True), ("manual_route_guidance", True),
        ("data_contract_hashes.action_data_hash", "0" * 64),
        ("execution_contract.explicit_only_stage_required", False),
    ]
    clean = {key: value for key, value in plan.items() if not key.startswith("_")}
    for dotted, value in mutations:
        mutated = copy.deepcopy(clean); target = mutated; parts = dotted.split(".")
        for part in parts[:-1]: target = target[int(part)] if part.isdigit() else target[part]
        if parts[-1].isdigit(): target[int(parts[-1])] = value
        else: target[parts[-1]] = value
        try: validate_mcts_plan(mutated)
        except ValueError: pass
        else: raise AssertionError(f"mutation accepted: {dotted}")
    print(f"mcts_plan_v118_3x50k_contract_smoke_test ok sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")


if __name__ == "__main__": main()
