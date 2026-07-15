from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/mcts_plan_v118_32gb_3x50k.json"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "search/run_mcts.py", "--plan", str(PLAN), *args], cwd=ROOT,
                          text=True, capture_output=True, timeout=30)


def main() -> None:
    dry = run("--dry-run-plan")
    assert dry.returncode == 0 and len(json.loads(dry.stdout)["stages"]) == 3
    gated = run("--execute")
    assert gated.returncode != 0 and "explicit --only-stage" in gated.stderr + gated.stdout
    unknown = run("--execute", "--only-stage", "not_a_stage")
    assert unknown.returncode != 0 and "Unknown/non-executable" in unknown.stderr + unknown.stdout
    print("mcts_v118_multistage_execution_gate_smoke_test ok explicit_only_stage=true")


if __name__ == "__main__": main()
