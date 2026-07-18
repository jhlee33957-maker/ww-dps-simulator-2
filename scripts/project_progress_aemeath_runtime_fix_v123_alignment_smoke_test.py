from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "122"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-122.zip"
    assert status["latest_verified_archive_sha256"] == "5620584500694b7be1552a74e0b8644c1e93fac381e7c18af55a6258ad3bebcf"
    assert status["current_candidate"] == "123"
    assert status["candidate_expected_next_archive"] == "ww-dps-simulator-2-123.zip"
    current = progress["current_in_progress_task"]
    runtime = current["candidate_123_aemeath_runtime_fix"]
    assert runtime["precombat_radiance_heavy_resolver_connected"] is True
    assert runtime["radiance_consumed_on_successful_charged_ii"] is True
    assert runtime["intro_starlume_acceleration_connected"] is True
    assert runtime["starlume_duration_combat_seconds"] == 15.0
    assert runtime["first_liberation_additional_resonance_rate_connected"] is True
    assert runtime["user_aemeath_segment_feasibility_verified"] is True
    assert runtime["account_manual_baseline_executed"] is False
    assert runtime["account_manual_baseline_authored_by_user"] == "pending"
    assert runtime["account_bc_ppo_beam_mcts_executed"] is False
    assert runtime["next_task"] == "receive the user's full exact combo and encode it as candidate 124 manual baseline"
    history = progress["candidate_history"]
    v122 = next(item for item in history if item.get("candidate") == "122")
    assert v122["status"] == "externally_verified_complete"
    assert v122["verified_archive_sha256"] == status["latest_verified_archive_sha256"]
    assert history[-1]["candidate"] == "123"
    assert history[-1]["status"] == "candidate_pending_external_review"
    print("project_progress_aemeath_runtime_fix_v123_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
