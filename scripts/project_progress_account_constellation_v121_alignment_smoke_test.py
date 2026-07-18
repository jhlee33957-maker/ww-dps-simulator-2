from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    assert status["latest_externally_verified_baseline"] == "120"
    assert status["latest_verified_archive"] == "ww-dps-simulator-2-120(1).zip"
    assert status["latest_verified_archive_sha256"] == "e61f7152726fdc7c05719c543cee67264a965af9d152c6e8de59d2f59f79b248"
    assert status["current_candidate"] == "121"
    assert status["current_task_status"] == "candidate_pending_external_review"
    current = progress["current_in_progress_task"]["candidate_121_account_constellations"]
    assert current["scope_id"] == "single_persistent_boss_no_kill_no_survival"
    assert current["mechanics_implemented"] is True
    assert current["account_party_created"] is False
    assert current["account_baseline_created"] is False
    assert current["training_search_or_evaluation_executed"] is False
    assert current["observation_version"] == "slot_account_constellation_single_boss_v6"
    assert current["legacy_benchmark_observation_version"] == "slot_generic_mechanics_v5"
    assert "Aemeath S5 all effects" in current["unsupported_effects"]
    print("project_progress_account_constellation_v121_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
