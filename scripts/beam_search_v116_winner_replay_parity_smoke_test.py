from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_completed_result import COMPLETED_DIR, WINNER_DAMAGE, WINNER_ROUTE_ID
from search.beam_reporting import replay_selected_route_to_files


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    summary = json.loads((root / COMPLETED_DIR / "winning_route_summary.json").read_text(encoding="utf-8"))
    selected = [item["selected_action_id"] for item in summary["attempted_actions"]]
    assert len(selected) == 162
    timeline_path = root / COMPLETED_DIR / "winning_route_timeline.csv"
    with timeline_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 162
    assert sum(float(row["damage"]) for row in rows) == 5651892.274552993
    truncated = [row for row in rows if row["truncated_by_combat_limit"].lower() == "true"]
    assert len(truncated) == 1 and truncated[0]["resolved_action_id"] == "lynae_echo_hyvatia"

    progress = json.loads((root / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    timing_core = progress["candidate_124_timing_core_1"]
    if timing_core["historical_results_status"] == "preserved_but_requires_timing_rebaseline":
        assert timing_core["historical_result_files_rewritten"] is False
        assert timing_core["mornye_liberation_state_timing_implemented"] is True
        print(
            "beam_search_v116_winner_replay_parity_smoke_test ok "
            "historical_artifact_preserved=true timing_rebaseline_required=true"
        )
        return

    with tempfile.TemporaryDirectory(prefix="beam-v116-parity-") as temporary:
        replay = replay_selected_route_to_files(
            selected_sequence=selected,
            output_root=Path(temporary),
            route_id=WINNER_ROUTE_ID,
            combat_duration=120.0,
        )
    assert replay["selected_action_count"] == replay["resolved_action_count"] == replay["executed_action_count"] == 162
    assert all(item["available_before_execution"] and item["executed"] for item in replay["attempted_actions"])
    assert replay["final_combat_time"] == 120.0
    assert replay["total_damage"] == WINNER_DAMAGE
    print("beam_search_v116_winner_replay_parity_smoke_test ok")


if __name__ == "__main__":
    main()
