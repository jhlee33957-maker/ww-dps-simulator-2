from __future__ import annotations
import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from search.mcts_plan import load_mcts_plan
from search.mcts_search import MCTSSearch
from scripts.mcts_v117_test_utils import directory_digest


def fixture(plan, simulations: int = 40):
    stage = copy.deepcopy(plan["stages"][0])
    stage.update(stage_id="retention_fixture", maximum_simulations=simulations, maximum_nodes=simulations + 2,
                 combat_duration=4.0, checkpoint_interval_simulations=10,
                 limit_check_interval_simulations=8, canonical_output_root="temporary_fixture_only")
    return stage


def generation_files(checkpoint: Path) -> set[str]:
    return {path.name for path in checkpoint.iterdir() if path.name.startswith(
        ("tree_", "mast_", "rng_", "completed_", "snapshot_index_"))}


def main() -> None:
    plan = load_mcts_plan(ROOT / "data/mcts_plan_v118_32gb_3x50k.json")
    raw = ROOT / "results/mcts_v117_32gb/calibration_20k_seed_117001"
    raw_before = directory_digest(raw)
    with tempfile.TemporaryDirectory(prefix="mcts-retention-") as tmp:
        root = Path(tmp); stage = fixture(plan)
        retained = MCTSSearch(plan=plan, stage=stage, output_root=root / "retained", allow_test_output_root=True).run()
        cp = root / "retained/checkpoint"
        assert len(generation_files(cp)) == 10
        assert all("00000030" in name or "00000040" in name for name in generation_files(cp))
        progression = json.loads((cp / "progression.json").read_text(encoding="utf-8"))
        assert [row["simulation_count"] for row in progression["checkpoints"]] == [10, 20, 30, 40]
        no_retention = copy.deepcopy(stage)
        no_retention.pop("checkpoint_retention_generations"); no_retention.pop("allow_corrupt_latest_fallback")
        full = MCTSSearch(plan=plan, stage=no_retention, output_root=root / "full", allow_test_output_root=True).run()
        assert retained["logical_result_sha256"] == full["logical_result_sha256"]
        assert retained["rng_final_state_sha256"] == full["rng_final_state_sha256"]
        partial_root = root / "fallback"
        MCTSSearch(plan=plan, stage=stage, output_root=partial_root, max_simulations=30, allow_test_output_root=True).run()
        latest = json.loads((partial_root / "checkpoint/latest_manifest.json").read_text(encoding="utf-8"))
        (partial_root / "checkpoint" / latest["files"]["tree"]["path"]).write_bytes(b"corrupt")
        resumed = MCTSSearch(plan=plan, stage=stage, output_root=partial_root, max_simulations=40,
                             allow_test_output_root=True).run(resume=True)
        assert resumed["resume_checkpoint_source"] == "previous" and resumed["resume_checkpoint_fallback_reason"]
        assert resumed["logical_result_sha256"] == retained["logical_result_sha256"]
        interrupted_root = root / "interrupted"
        first = MCTSSearch(plan=plan, stage=stage, output_root=interrupted_root, max_simulations=20,
                           allow_test_output_root=True)
        first.run()
        runner = MCTSSearch(plan=plan, stage=stage, output_root=interrupted_root, max_simulations=30,
                            allow_test_output_root=True)
        def interrupted(*_args, **_kwargs): raise RuntimeError("injected after manifest commit before prune")
        runner.checkpoints._commit_progression_and_prune = interrupted
        try: runner.run(resume=True)
        except RuntimeError as error: assert "before prune" in str(error)
        else: raise AssertionError("interrupted commit injection did not fire")
        assert all((interrupted_root / "checkpoint" / f"{prefix}_00000020{suffix}").exists()
                   for prefix, suffix in (("tree", ".npz"), ("mast", ".npz"), ("rng", ".json"),
                                          ("completed", ".json"), ("snapshot_index", ".json")))
    assert directory_digest(raw) == raw_before
    print("mcts_checkpoint_generation_retention_smoke_test ok generations=2 logical_identical=true fallback=previous")


if __name__ == "__main__": main()
