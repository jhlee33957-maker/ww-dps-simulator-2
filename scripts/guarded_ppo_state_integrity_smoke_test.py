from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import (
        build_best_manifest,
        build_leaderboard,
        create_initial_state,
        ensure_step_zero_records,
        load_plan,
        select_best_candidate,
        verify_resume_state,
        write_json_atomic,
    )

    plan_path = ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"
    plan = load_plan(plan_path)
    with tempfile.TemporaryDirectory(prefix="guarded-state-integrity-") as temp_dir:
        root = Path(temp_dir)
        results_root = root / plan["results_root"]
        state_path = results_root / "experiment_state.json"
        state = create_initial_state(plan, plan_path=plan_path, output_root=root, smoke_run=False)
        write_json_atomic(state_path, state)
        assert state_path.exists()
        ensure_step_zero_records(
            plan,
            state=state,
            output_root=root,
            state_path=state_path,
            evaluation_timeout_seconds=120,
        )
        step0_records = [
            chunk
            for branch_state in state["branches"].values()
            for chunk in branch_state["chunks"]
            if chunk.get("kind") == "guarded_ppo_step0_verified_bc_alias"
        ]
        assert len(step0_records) == 2
        assert len({item["summary_path"] for item in step0_records}) == 1
        state["global_best"] = build_best_manifest(step0_records[0], reason="tampered")
        state["global_best"]["total_damage"] = -1
        write_json_atomic(state_path, state)
        verify_resume_state(state, plan_path=plan_path, plan=plan, output_root=root, state_path=state_path, results_root=results_root)
        repaired = json.loads(state_path.read_text(encoding="utf-8"))
        recomputed = build_best_manifest(select_best_candidate([*repaired["incumbents"], *step0_records]), reason="ignored")
        assert repaired["global_best"]["total_damage"] == recomputed["total_damage"]
        leaderboard = build_leaderboard(repaired)
        assert leaderboard["global_best"]["winner_kind"] == "verified_bc_model"

        duplicate = json.loads(state_path.read_text(encoding="utf-8"))
        first_branch = next(iter(duplicate["branches"].values()))
        first_branch["chunks"].append(dict(first_branch["chunks"][0]))
        try:
            verify_resume_state(duplicate, plan_path=plan_path, plan=plan, output_root=root)
        except ValueError as exc:
            assert "Duplicate" in str(exc)
        else:
            raise AssertionError("duplicate chunk record was not rejected")
    print("guarded_ppo_state_integrity_smoke_test ok")


if __name__ == "__main__":
    main()
