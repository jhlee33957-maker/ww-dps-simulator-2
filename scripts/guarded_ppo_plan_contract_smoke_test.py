from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import DEFAULT_PLAN_PATH, run_dry_run_plan, sha256_file, validate_plan

    plan = json.loads(DEFAULT_PLAN_PATH.read_text(encoding="utf-8"))
    result = validate_plan(plan, plan_path=DEFAULT_PLAN_PATH)
    assert result["status"] == "ok"
    assert result["plan_sha256"] == sha256_file(DEFAULT_PLAN_PATH)
    assert result["branch_ids"] == [
        "bc_conservative_seed_11",
        "bc_exploratory_seed_73",
        "scratch_control_seed_137",
    ]
    assert [branch["seed"] for branch in plan["branches"]] == [11, 73, 137]
    assert [branch["learning_rate"] for branch in plan["branches"]] == [0.0001, 0.0003, 0.0003]
    assert [branch["ent_coef"] for branch in plan["branches"]] == [0.005, 0.02, 0.02]
    assert all(branch["initial_active_character"] == "aemeath" for branch in plan["branches"])
    assert all(branch["curriculum_reset_mode"] == "none" for branch in plan["branches"])
    assert all(branch["continuation_mode"] == "continue_from_latest_branch_checkpoint" for branch in plan["branches"])
    assert all(branch["total_timesteps"] == 100000 for branch in plan["branches"])
    assert all(branch["chunk_timesteps"] == 10000 for branch in plan["branches"])
    assert plan["evaluation_after_every_chunk"] is True
    assert plan["branch_independence"] is True
    assert plan["global_optimum_claimed"] is False
    assert plan["route_similarity_objective"] is False
    assert plan["character_specific_reward"] is False
    assert plan["bc_refresh_enabled"] is False
    assert plan["rollback_enabled"] is False
    dry_run = run_dry_run_plan(DEFAULT_PLAN_PATH)
    assert dry_run["status"] == "dry_run_plan_ok"
    assert len(dry_run["future_commands"]) == 31
    assert "step_0_shared_evaluation" in dry_run["future_commands"][0]
    assert len(dry_run["future_commands"][0]["step_0_aliases"]) == 2
    assert len(dry_run["incumbent_records"]) == 3
    assert dry_run["canonical_models_created"] is False
    assert dry_run["canonical_results_created"] is False
    assert not (ROOT / "models" / "guarded_ppo_v109").exists()
    assert not (ROOT / "results" / "guarded_ppo_v109").exists()
    for mutation in (
        ("branches", 0, "seed", 99),
        ("branches", 1, "learning_rate", 0.123),
        ("branches", 2, "continuation_mode", "global_best"),
    ):
        bad = json.loads(json.dumps(plan))
        section, index, key, value = mutation
        bad[section][index][key] = value
        try:
            validate_plan(bad, plan_path=DEFAULT_PLAN_PATH)
        except ValueError:
            pass
        else:
            raise AssertionError(f"plan mutation unexpectedly passed: {mutation}")
    print("guarded_ppo_plan_contract_smoke_test ok")


if __name__ == "__main__":
    main()
