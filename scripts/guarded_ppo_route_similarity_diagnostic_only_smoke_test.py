from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "guarded_ppo_v109"


def main() -> None:
    state = _load_json(RESULTS / "experiment_state.json")
    leaderboard = _load_json(RESULTS / "leaderboard.json")
    best = _load_json(RESULTS / "best_checkpoint.json")
    final_summary = _load_json(RESULTS / "final_experiment_summary.json")

    assert final_summary["objective"] == "deterministic_120s_total_damage_only"
    assert final_summary["route_similarity_objective"] is False
    assert final_summary["route_similarity_usage"] == "diagnostic_only_not_used_for_winner_selection"
    assert final_summary["winner"]["selection_rule"] == "Verified immutable incumbent wins exact/tolerance ties."
    assert best["winner_selection_reason"] == "completed guarded PPO v109 ingestion; verified immutable BC tie rule"
    assert leaderboard["objective"] == "deterministic_120s_total_damage_only"

    records = _records(state)
    assert any("route_agreement_ratio_diagnostic_only" in record for record in records)
    assert all("route_similarity_reward" not in json.dumps(record, sort_keys=True) for record in records)
    damage_sorted = sorted(records, key=lambda item: float(item["total_damage"]), reverse=True)
    assert damage_sorted[0]["winner_kind"] in {"manual_baseline", "verified_bc_model", "guarded_ppo_step0_verified_bc_alias"}
    assert best["winner_kind"] == "verified_bc_model"
    assert final_summary["winner"]["winner_kind"] == "verified_bc_model"
    guarded = [record for record in records if record.get("kind") == "guarded_ppo_checkpoint"]
    assert max(float(record["total_damage"]) for record in guarded) <= float(final_summary["winner"]["total_damage"]) + 1e-6
    print("guarded_ppo_route_similarity_diagnostic_only_smoke_test ok")


def _records(state: dict[str, Any]) -> list[dict[str, Any]]:
    records = list(state["incumbents"])
    for branch_state in state["branches"].values():
        records.extend(item for item in branch_state["chunks"] if item.get("status") == "completed")
    return records


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
