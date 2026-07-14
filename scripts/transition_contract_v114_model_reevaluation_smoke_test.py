from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    leaderboard = json.loads(
        (ROOT / "results/transition_contract_v114_model_reevaluation/leaderboard.json").read_text(encoding="utf-8")
    )
    assert leaderboard["schema_version"] == "transition_contract_v114_model_reevaluation_leaderboard"
    assert leaderboard["evaluation_count"] == 32
    assert all(row["completed_120s"] for row in leaderboard["rankings"])
    assert all(row["invalid_action_count"] == 0 for row in leaderboard["rankings"])
    assert leaderboard["winner"]["total_damage"] == max(row["total_damage"] for row in leaderboard["rankings"])
    assert leaderboard["winner"]["model_path"] == "models/guarded_ppo_v109/bc_conservative_seed_11/step_000090000.zip"
    assert leaderboard["winner"]["total_damage"] == 5276844.358692044
    assert leaderboard["winner"]["dps"] == 43973.70298910037
    assert leaderboard["winner"]["selected_route_sha256"] == "27920c26c93bc51aacb964211062b301a2af16b899e2bbafc442edca17e72c54"
    assert leaderboard["winner"]["resolved_route_sha256"] == "350df3b0df184b5d9e8c5cecffef7893ddb53f6d31eeaf864bf7c61fb71590f0"
    assert leaderboard["winner"]["aemeath_outro_cast_count"] == 3
    assert leaderboard["winner"]["aemeath_outro_upgrade_count"] == 3
    assert all(row["aemeath_outro_upgrade_count"] <= row["aemeath_outro_cast_count"] for row in leaderboard["rankings"])
    assert all(row["aemeath_outro_cast_count"] != 6 for row in leaderboard["rankings"])
    comparison = json.loads((ROOT / "results/manual_model_comparison_v114.json").read_text(encoding="utf-8"))
    assert comparison["current_best"]["total_damage"] == max(
        entry["total_damage"] for entry in comparison["entries"] if entry["completed_120s"]
    )
    assert comparison["training_executed"] is False
    print("transition_contract_v114_model_reevaluation_smoke_test ok")


if __name__ == "__main__":
    main()
