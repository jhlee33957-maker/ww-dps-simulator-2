from __future__ import annotations

from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import (
        build_best_manifest,
        build_incumbent_records,
        create_initial_state,
        load_plan,
        select_best_candidate,
    )

    plan_path = ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"
    plan = load_plan(plan_path)
    records = build_incumbent_records(plan, output_root=ROOT)
    assert [record["incumbent_id"] for record in records] == ["manual_baseline", "bc_model", "regressed_ppo_100k"]
    best = select_best_candidate(records)
    assert best["kind"] == "verified_bc_model"
    assert best["model_path"] == "models/maskable_ppo_bc_v105.zip"
    assert best["externally_verified"] is True

    near_tie_unverified = dict(best)
    near_tie_unverified.update(
        {
            "kind": "guarded_ppo_checkpoint",
            "winner_kind": "guarded_ppo_checkpoint",
            "externally_verified": False,
            "immutable_model": True,
            "declared_order": 999,
            "total_damage": float(best["total_damage"]) + 5e-7,
        }
    )
    assert select_best_candidate([best, near_tie_unverified])["kind"] == "verified_bc_model"

    higher = dict(near_tie_unverified)
    higher["total_damage"] = float(best["total_damage"]) + 2e-6
    assert select_best_candidate([best, higher])["kind"] == "guarded_ppo_checkpoint"

    with tempfile.TemporaryDirectory(prefix="guarded-incumbent-") as temp_dir:
        output_root = Path(temp_dir)
        initial_state = create_initial_state(plan, plan_path=plan_path, output_root=output_root, smoke_run=False)
        global_best = initial_state["global_best"]
        assert global_best["winner_kind"] == "verified_bc_model"
        assert global_best["model_path"] == "models/maskable_ppo_bc_v105.zip"
        assert global_best["global_optimum_proven"] is False
        assert global_best["evaluation_summary_path"] == "results/ppo_evaluation_summary.json"
    assert not (ROOT / "models" / "guarded_ppo_v109" / "best.zip").exists()

    manifest = build_best_manifest(best, reason="unit smoke")
    for key in (
        "winner_kind",
        "model_path",
        "model_sha256",
        "total_damage",
        "dps",
        "evaluation_summary_path",
        "manual_baseline_damage_ratio",
        "bc_damage_ratio",
        "global_optimum_proven",
    ):
        assert key in manifest
    print("guarded_ppo_incumbent_best_retention_smoke_test ok")


if __name__ == "__main__":
    main()
