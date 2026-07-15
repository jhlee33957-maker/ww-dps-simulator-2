from __future__ import annotations

import copy
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from search.mcts_plan import load_mcts_plan
from search.mcts_search import MCTSSearch


def inventory(root: Path) -> tuple[tuple[str, int, str], ...]:
    if not root.is_dir():
        return ()
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append(
            (
                path.relative_to(root).as_posix(),
                path.stat().st_size,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    return tuple(rows)


def bounded_stage(source: dict) -> dict:
    stage = copy.deepcopy(source)
    stage.update(
        maximum_simulations=2,
        maximum_nodes=4,
        combat_duration=4.0,
        checkpoint_interval_simulations=2,
        canonical_output_root="temporary_fixture_only",
    )
    return stage


def main() -> None:
    plan = load_mcts_plan(ROOT / "data/mcts_plan_v118_32gb_3x50k.json")
    canonical_roots = [ROOT / stage["canonical_output_root"] for stage in plan["stages"]]
    assert len(set(canonical_roots)) == 3
    assert all(str(stage["seed"]) in stage["canonical_output_root"] for stage in plan["stages"])
    raw_before = {str(root): inventory(root) for root in canonical_roots if root.is_dir()}
    raw_present = bool(raw_before)

    with tempfile.TemporaryDirectory(prefix="mcts-seed-isolation-") as tmp:
        first = bounded_stage(plan["stages"][0])
        second = bounded_stage(plan["stages"][1])
        assert first["seed"] != second["seed"]
        out1, out2 = Path(tmp) / str(first["seed"]), Path(tmp) / str(second["seed"])
        assert out1 != out2

        one = MCTSSearch(plan=plan, stage=first, output_root=out1, allow_test_output_root=True).run()
        first_before_second = inventory(out1)
        two = MCTSSearch(plan=plan, stage=second, output_root=out2, allow_test_output_root=True).run()
        assert first_before_second == inventory(out1), "second seed mutated first seed output"
        assert inventory(out2), "second bounded seed produced no fixture output"
        assert one["rng_final_state_sha256"] != two["rng_final_state_sha256"]
        assert one["logical_result_sha256"] != two["logical_result_sha256"]

        cross_seed_root = Path(tmp) / "cross-seed-resume"
        shutil.copytree(out1, cross_seed_root)
        try:
            MCTSSearch(
                plan=plan,
                stage=second,
                output_root=cross_seed_root,
                allow_test_output_root=True,
            ).run(resume=True)
        except ValueError as error:
            assert "stage hash mismatch" in str(error) or "previous checkpoint is unusable" in str(error)
        else:
            raise AssertionError("cross-seed resume was accepted")

    raw_after = {str(root): inventory(root) for root in canonical_roots if root.is_dir()}
    assert raw_before == raw_after, "bounded fixture mutated canonical raw production output"
    print(
        "mcts_v118_seed_output_isolation_smoke_test ok "
        f"roots=2 seeds={first['seed']},{second['seed']} cross_seed_resume_rejected=true "
        f"raw_present={str(raw_present).lower()} raw_root_count={len(raw_before)}"
    )


if __name__ == "__main__":
    main()
