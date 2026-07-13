from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import DEFAULT_PLAN_PATH, create_initial_state, ensure_step_zero_records, load_plan, run_dry_run_plan, write_json_atomic

    plan = load_plan(DEFAULT_PLAN_PATH)
    dry = run_dry_run_plan(DEFAULT_PLAN_PATH)
    shared = [item for item in dry["future_commands"] if "step_0_shared_evaluation" in item]
    assert len(shared) == 1
    assert not any("step_0_evaluation" in item for item in dry["future_commands"])
    command = shared[0]
    assert [alias["branch_id"] for alias in command["step_0_aliases"]] == [
        "bc_conservative_seed_11",
        "bc_exploratory_seed_73",
    ]
    summary_path = command["step_0_shared_evaluation"]["summary_path"]
    timeline_path = command["step_0_shared_evaluation"]["timeline_path"]
    assert summary_path.endswith("results/guarded_ppo_v109/step_000000000_verified_bc_alias_summary.json")
    assert timeline_path.endswith("results/guarded_ppo_v109/step_000000000_verified_bc_alias_timeline.csv")
    assert all(alias["summary_path"] == summary_path for alias in command["step_0_aliases"])
    assert all(alias["timeline_path"] == timeline_path for alias in command["step_0_aliases"])

    with tempfile.TemporaryDirectory(prefix="guarded-step0-alias-") as temp_dir:
        root = Path(temp_dir)
        state_path = root / plan["results_root"] / "experiment_state.json"
        state = create_initial_state(plan, plan_path=DEFAULT_PLAN_PATH, output_root=root, smoke_run=False)
        write_json_atomic(state_path, state)
        ensure_step_zero_records(plan, state=state, output_root=root, state_path=state_path, evaluation_timeout_seconds=120)
        completed = [
            chunk
            for branch_state in state["branches"].values()
            for chunk in branch_state["chunks"]
            if chunk.get("kind") == "guarded_ppo_step0_verified_bc_alias"
        ]
        assert len(completed) == 2
        assert len({item["summary_path"] for item in completed}) == 1
        assert len({item["timeline_path"] for item in completed}) == 1
        assert completed[0]["summary_path"].endswith("step_000000000_verified_bc_alias_summary.json")
        assert completed[0]["timeline_path"].endswith("step_000000000_verified_bc_alias_timeline.csv")
        persisted = json.loads(state_path.read_text(encoding="utf-8"))
        assert persisted["global_best"]["winner_kind"] == "verified_bc_model"
    print("guarded_ppo_dry_run_step0_alias_smoke_test ok")


if __name__ == "__main__":
    main()
