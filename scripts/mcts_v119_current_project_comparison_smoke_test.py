from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "results/mcts_v118_production_3x50k_v119/comparison.json").read_text(encoding="utf-8"))
    assert len(payload["candidates"]) == 8
    assert payload["selection"] == "maximum_deterministic_completed_120s_total_damage_only"
    assert payload["overall_project_winner"]["kind"] == "beam"
    assert payload["overall_project_winner"]["route_id"] == "67a4250b3b8d0de9"
    assert payload["best_trained_model"]["method"] == "guarded PPO 90k"
    assert payload["best_mcts_production_result"]["seed"] == 118003
    assert payload["partial_routes_compete"] is False and payload["global_optimum_proven"] is False
    print("mcts_v119_current_project_comparison_smoke_test ok candidates=8 winner=beam best_model=guarded_ppo_90k")


if __name__ == "__main__": main()
