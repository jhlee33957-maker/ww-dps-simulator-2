from __future__ import annotations
import copy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from search.mcts_plan import load_mcts_plan
from search.mcts_search import MCTSSearch


def main() -> None:
    plan = load_mcts_plan(ROOT / "data/mcts_plan_v118_32gb_3x50k.json")
    roots = [stage["canonical_output_root"] for stage in plan["stages"]]
    assert len(set(roots)) == 3 and all(str(stage["seed"]) in stage["canonical_output_root"] for stage in plan["stages"])
    with tempfile.TemporaryDirectory(prefix="mcts-seed-isolation-") as tmp:
        first, second = (copy.deepcopy(plan["stages"][index]) for index in (0, 1))
        for stage in (first, second):
            stage.update(maximum_simulations=2, maximum_nodes=4, combat_duration=4.0,
                         checkpoint_interval_simulations=2, canonical_output_root="temporary_fixture_only")
        out1, out2 = Path(tmp) / "118001", Path(tmp) / "118002"
        one = MCTSSearch(plan=plan, stage=first, output_root=out1, allow_test_output_root=True).run()
        before = sorted(path.relative_to(out1).as_posix() for path in out1.rglob("*"))
        two = MCTSSearch(plan=plan, stage=second, output_root=out2, allow_test_output_root=True).run()
        assert before == sorted(path.relative_to(out1).as_posix() for path in out1.rglob("*"))
        assert one["rng_final_state_sha256"] != two["rng_final_state_sha256"] and out1 != out2
    assert not any((ROOT / path).exists() for path in roots)
    print("mcts_v118_seed_output_isolation_smoke_test ok roots=3 cross_seed=false")


if __name__ == "__main__": main()
