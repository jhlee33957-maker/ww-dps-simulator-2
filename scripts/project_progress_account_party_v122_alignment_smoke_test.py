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
    assert status["latest_externally_verified_baseline"] == "121"
    assert status["current_candidate"] == "122"
    assert status["current_task_status"] == "candidate_pending_external_review"
    current = progress["current_in_progress_task"]
    assert current["account_party_id"] == "aemeath_mornye_lynae_account_actual_01"
    assert current["initial_active_character"] == "mornye"
    assert current["aemeath_resonance_mode"] == "tune_rupture"
    assert current["precombat_elapsed_seconds"] == 4.01
    assert current["aemeath_s1_precombat_radiance"] == "enabled"
    assert current["lynae_s1_precombat_overflow"] == 120
    assert current["account_party_configuration_ready"] is True
    assert current["account_manual_baseline_executed"] is False
    assert current["account_bc_ppo_beam_mcts_executed"] is False
    assert current["benchmark_winner"] == "Beam"
    assert current["global_optimum_claimed"] is False
    assert current["next_task"] == "create a new account-specific manual baseline from scratch"
    history = progress["candidate_history"]
    v121 = next(item for item in history if item.get("candidate") == "121")
    assert v121["status"] == "externally_verified_complete"
    assert v121["verified_archive_sha256"] == "2a031ff8662f0c929305393558191059f4c61ff28e7a06c004e3b9b3e94920fa"
    assert history[-1]["candidate"] == "122"
    assert history[-1]["status"] == "candidate_pending_external_review"
    print("project_progress_account_party_v122_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
