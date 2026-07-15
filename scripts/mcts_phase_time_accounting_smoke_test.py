from __future__ import annotations
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from search.mcts_search import MCTSSearch
from scripts.mcts_v117_test_utils import plan_and_stage


def main() -> None:
    plan, stage = plan_and_stage(simulations=1, combat_duration=4.0, checkpoint_interval=10)
    with tempfile.TemporaryDirectory(prefix="mcts-phase-") as tmp:
        runner = MCTSSearch(plan=plan, stage=stage, output_root=Path(tmp), allow_test_output_root=True)
        original = runner._execute_slot
        calls = 0
        def delayed(simulation, slot):
            nonlocal calls
            calls += 1
            if calls == 1: time.sleep(0.04)
            return original(simulation, slot)
        runner._execute_slot = delayed
        result = runner.run()
        phase = result["invocation_phase_seconds"]
        assert phase["expansion"] >= 0.035 and phase["selection"] < 0.025, phase
        assert sum(phase.values()) <= result["elapsed_seconds"] + 0.01
        assert result["phase_time_accounting"] == "mutually_exclusive_v118"
    print("mcts_phase_time_accounting_smoke_test ok mutually_exclusive=true")


if __name__ == "__main__": main()
