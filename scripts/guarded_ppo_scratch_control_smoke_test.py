from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import build_future_commands, load_plan

    plan_path = ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"
    plan = load_plan(plan_path)
    scratch = plan["branches"][2]
    assert scratch["branch_id"] == "scratch_control_seed_137"
    assert scratch["initialization"]["mode"] == "scratch"
    assert scratch["initialization"]["source_model_path"] is None
    commands = build_future_commands(plan, plan_path=plan_path, output_root=ROOT)
    scratch_first = next(item for item in commands if item.get("branch_id") == "scratch_control_seed_137" and item["chunk_index"] == 1)
    assert scratch_first["continuation_parent"] is None
    assert "--load-model" not in scratch_first["train"]
    bc_first = next(item for item in commands if item.get("branch_id") == "bc_conservative_seed_11" and item["chunk_index"] == 1)
    assert bc_first["continuation_parent"] == "models/maskable_ppo_bc_v105.zip"
    assert "--load-model" in bc_first["train"]
    print("guarded_ppo_scratch_control_smoke_test ok")


if __name__ == "__main__":
    main()
