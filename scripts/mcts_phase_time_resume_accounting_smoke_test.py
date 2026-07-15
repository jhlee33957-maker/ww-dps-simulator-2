from __future__ import annotations
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from search.mcts_search import MCTSSearch
from scripts.mcts_v117_test_utils import plan_and_stage


def main() -> None:
    plan, stage = plan_and_stage(simulations=30, combat_duration=4.0, checkpoint_interval=10)
    with tempfile.TemporaryDirectory(prefix="mcts-phase-resume-") as tmp:
        root = Path(tmp)
        full = MCTSSearch(plan=plan, stage=stage, output_root=root / "full", allow_test_output_root=True).run()
        first = MCTSSearch(plan=plan, stage=stage, output_root=root / "resume", max_simulations=10, allow_test_output_root=True).run()
        resumed = MCTSSearch(plan=plan, stage=stage, output_root=root / "resume", max_simulations=30, allow_test_output_root=True).run(resume=True)
        assert full["logical_result_sha256"] == resumed["logical_result_sha256"]
        assert full["rng_final_state_sha256"] == resumed["rng_final_state_sha256"]
        assert full["mast_logical_sha256"] == resumed["mast_logical_sha256"]
        assert all(resumed["cumulative_phase_seconds"][key] >= first["cumulative_phase_seconds"][key] for key in first["cumulative_phase_seconds"])
        assert resumed["invocation_phase_seconds"] != resumed["cumulative_phase_seconds"]
        assert sum(resumed["invocation_phase_seconds"].values()) <= resumed["elapsed_seconds"] + 0.01
    print("mcts_phase_time_resume_accounting_smoke_test ok logical_unchanged=true")


if __name__ == "__main__": main()
