from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run_state_integrity_contract() -> None:
    from rl.guarded_ppo import (
        build_best_manifest,
        build_leaderboard,
        create_initial_state,
        load_plan,
        populate_step_zero_alias_records_from_verified_artifacts,
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
        # This is a state-contract guard, not another evaluator lifecycle.  Copy the
        # already-verified BC evaluation artifacts into the temporary step-0 alias
        # location so the pure helper validates record construction only.
        alias_summary = results_root / "step_000000000_verified_bc_alias_summary.json"
        alias_timeline = results_root / "step_000000000_verified_bc_alias_timeline.csv"
        alias_summary.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "results" / "ppo_evaluation_summary.json", alias_summary)
        shutil.copyfile(ROOT / "results" / "ppo_timeline.csv", alias_timeline)
        alias_summary_data = json.loads(alias_summary.read_text(encoding="utf-8"))
        alias_summary_data["model_training_metadata_source"] = "bc_model_sidecar"
        alias_summary.write_text(json.dumps(alias_summary_data, indent=2) + "\n", encoding="utf-8", newline="\n")
        populate_step_zero_alias_records_from_verified_artifacts(
            plan,
            state=state,
            output_root=root,
            state_path=state_path,
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


def main() -> None:
    run_state_integrity_contract()
    print("guarded_ppo_state_integrity_smoke_test ok")


if __name__ == "__main__":
    main()
