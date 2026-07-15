from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_completed_result import validate_calibration


def main() -> None:
    compact = ROOT / "results/mcts_v117_calibration_20k_v118"
    manifest = json.loads((compact / "result_manifest.json").read_text(encoding="utf-8"))
    inv = manifest["full_inventory"]
    assert (inv["file_count"], inv["total_bytes"], inv["normalized_entry_digest_sha256"]) == (
        111, 38944560, "b959d86ca0e4657e6dd918340eef87a520b02ea158bb30f661928f81b204e0b7")
    assert manifest["plan"]["sha256"] == "4d69880283f7a2fe837631fece76cd5eb06e62af544b31e9ea6c96f1a82f11bb"
    calibration = manifest["calibration"]
    assert (calibration["simulations"], calibration["completed_rollouts"], calibration["invalid_rollouts"],
            calibration["node_count"], calibration["retained_routes"]) == (20000, 20000, 0, 20001, 128)
    winner = calibration["winner"]
    assert winner["route_id"] == "5aab329ce5b526a7" and winner["total_damage"] == 4128137.812582737
    assert winner["dps"] == 34401.14843818948
    assert winner["selected_sequence_sha256"] == "5aab329ce5b526a709d530ae0a3037d4e8e776dff7726bfa0ecc4b02ca83116c"
    assert winner["resolved_sequence_sha256"] == "bccd12d7c852d65e168e4ead82fd6fb2514d4d856e865db41a74620699316e1d"
    board = json.loads((compact / "leaderboard.json").read_text(encoding="utf-8"))
    assert len(board["routes"]) == 128 and all(route["combat_time"] == 120.0 for route in board["routes"])
    assert [(-route["total_damage"], route["selected_sequence_sha256"]) for route in board["routes"]] == sorted(
        (-route["total_damage"], route["selected_sequence_sha256"]) for route in board["routes"])
    summary = json.loads((compact / "final_summary.json").read_text(encoding="utf-8"))
    assert summary["calibration_only"] and not summary["production_mcts_executed"] and not summary["global_optimum_proven"]
    assert summary["current_overall_winner"] == "completed_beam_route_67a4250b3b8d0de9"
    raw = ROOT / manifest["source_raw_output_path"]
    if raw.is_dir():
        validate_calibration(ROOT, raw)
    print("mcts_v117_20k_calibration_integrity_smoke_test ok files=111 bytes=38944560 routes=128")


if __name__ == "__main__": main()
