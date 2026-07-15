from __future__ import annotations

import copy
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_plan import HARD_MEMORY_BUDGET, load_mcts_plan, validate_mcts_plan


def main() -> None:
    root = Path(__file__).resolve().parents[1]; path = root / "data/mcts_plan_v117_32gb.json"; plan = load_mcts_plan(path)
    assert plan["stages"][0]["memory_budget_bytes"] == HARD_MEMORY_BUDGET
    mutations = [
        ("algorithm", "bad"), ("objective", "bad"), ("manual_route_guidance", True), ("beam_route_guidance", True),
        ("data_contract_hashes.action_data_hash", "0" * 64), ("uct.exploration_constant", 1.0),
        ("reward.terminal_scale", 1.0), ("progressive_widening.coefficient", 3.0),
        ("mast.uniform_warmup_simulations", 999), ("mast.epsilon", 0.1), ("mast.minimum_visits", 3),
        ("mast.context", "action"), ("stages.0.seed", 1), ("stages.0.maximum_simulations", 19999),
        ("stages.0.maximum_nodes", 25000), ("stages.0.snapshot_stride", 7),
        ("stages.0.maximum_actions_per_simulation", 511), ("stages.0.maximum_consecutive_zero_time_actions", 31),
        ("stages.0.memory_budget_bytes", HARD_MEMORY_BUDGET + 1), ("stages.0.canonical_output_root", "bad"),
    ]
    for dotted, value in mutations:
        mutated = copy.deepcopy({k: v for k, v in plan.items() if not k.startswith("_")}); parts = dotted.split("."); target = mutated
        for part in parts[:-1]: target = target[int(part)] if part.isdigit() else target[part]
        target[parts[-1]] = value
        try: validate_mcts_plan(mutated)
        except ValueError: pass
        else: raise AssertionError(f"mutation accepted: {dotted}")
    print(f"mcts_plan_v117_32gb_contract_smoke_test ok sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")


if __name__ == "__main__": main()
