from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_plan import load_mcts_plan, stage_contract_hash
from search.mcts_reporting import write_mcts_results
from search.mcts_search import MCTSSearch


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Deterministic state UCT + per-seed MAST runner (candidate 117)")
    value.add_argument("--plan", type=Path, required=True); value.add_argument("--dry-run-plan", action="store_true")
    value.add_argument("--execute", action="store_true"); value.add_argument("--resume", action="store_true")
    value.add_argument("--only-stage"); value.add_argument("--max-simulations", type=int); value.add_argument("--output-root", type=Path)
    value.add_argument("--memory-budget-bytes", type=int)
    return value


def main() -> None:
    args = parser().parse_args(); plan_path = args.plan.resolve(); plan = load_mcts_plan(plan_path)
    plan["_plan_path"] = plan_path.relative_to(ROOT).as_posix() if plan_path.is_relative_to(ROOT) else plan_path.as_posix()
    stages = list(plan["stages"])
    if args.execute and len(stages) > 1 and not args.only_stage:
        raise SystemExit("Multi-stage MCTS production execution requires explicit --only-stage")
    if args.only_stage:
        matches = [item for item in stages if item["stage_id"] == args.only_stage]
        if len(matches) != 1: raise SystemExit(f"Unknown/non-executable stage: {args.only_stage}")
        stage = matches[0]
    else:
        stage = stages[0]
    dry = {"schema_version": plan["schema_version"], "candidate": plan["candidate"], "algorithm": plan["algorithm"],
           "plan_sha256": plan["_plan_sha256"], "stage_contract_sha256": stage_contract_hash(plan, stage), "stage": stage,
           "stages": stages,
           "execution_requested": bool(args.execute), "calibration_executed": False, "global_optimum_proven": False}
    if args.dry_run_plan or not args.execute:
        print(json.dumps(dry, indent=2)); return
    output_root = (args.output_root or (ROOT / stage["canonical_output_root"])).resolve()
    runner = MCTSSearch(plan=plan, stage=stage, output_root=output_root, max_simulations=args.max_simulations,
                        memory_budget_bytes=args.memory_budget_bytes)
    result = runner.run(resume=args.resume); result["_completed_routes"] = runner.completed_routes
    written = write_mcts_results(
        output_root,
        result,
        plan_path=plan_path,
        plan_sha256=plan["_plan_sha256"],
        stage=stage,
    )
    print(json.dumps({"termination_status": result["termination_status"], "simulations_completed": result["simulations_completed"],
                      "completed_rollout_count": result["completed_rollout_count"], "best_completed_route": result["best_completed_route"],
                      "logical_result_sha256": result["logical_result_sha256"], "output_root": output_root.as_posix()}, indent=2))


if __name__ == "__main__": main()
