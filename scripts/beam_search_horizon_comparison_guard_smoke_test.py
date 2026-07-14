from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_reporting import replay_selected_route_to_files, select_damage_only_winner  # noqa: E402
from search.beam_search import _leaderboard_payload  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-horizon-") as temp_dir:
        output = Path(temp_dir)
        short = replay_selected_route_to_files(
            selected_sequence=["aemeath_basic_attack"],
            output_root=output,
            combat_duration=3.0,
        )
        calibration = replay_selected_route_to_files(
            selected_sequence=["aemeath_basic_attack", "aemeath_basic_attack"],
            output_root=output,
            route_id="calibration_30s_probe",
            combat_duration=30.0,
        )
        manual_route = json.loads((ROOT / "data" / "manual_120s_baseline_routes_v104.json").read_text(encoding="utf-8-sig"))
        full = replay_selected_route_to_files(
            selected_sequence=list(manual_route["routes"]["primary"]["selected_policy_actions"]),
            output_root=output,
            route_id="full_120s_probe",
            combat_duration=120.0,
        )
    for summary in (short, calibration):
        assert summary["reference_damage_comparison_status"] == "horizon_mismatch_not_comparable"
        assert summary["comparison_against_references"]["numeric_total_damage_ranking"] is None
        assert "manual_bc_damage_delta" not in summary["route_comparison"]
        assert "manual_bc_damage_ratio" not in summary["route_comparison"]
        assert summary["route_comparison"]["reference_horizon_seconds"] == 120.0
    assert full["reference_damage_comparison_status"] == "comparable_120s_completed_route"
    assert "manual_bc_damage_delta" in full["route_comparison"]
    assert "manual_bc_damage_ratio" in full["route_comparison"]
    assert full["comparison_against_references"]["verified_bc"]["winner_kind"] == "verified_bc_model"
    calibration_leaderboard = _leaderboard_payload({"completed_routes": [full], "best_partial_frontier_node": None}, "calibration_30s", result_scope="calibration_horizon_only")
    assert calibration_leaderboard["winner"] is None
    assert calibration_leaderboard["calibration_only_no_project_winner"] is True
    equal_or_lower = select_damage_only_winner(
        [{"winner_kind": "beam_search_route", "total_damage": 5165134.682363356, "declared_order": 1}]
    )
    assert equal_or_lower["winner_kind"] == "verified_bc_model"
    print("beam_search_horizon_comparison_guard_smoke_test ok")


if __name__ == "__main__":
    main()
