from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress["status"]
    current = progress["current_in_progress_task"]
    history = next(item for item in progress["candidate_history"] if item.get("candidate") == "115")
    assert status["latest_externally_verified_baseline"] == "115"
    assert status["current_candidate"] == "116" and status["current_task_status"] == "candidate_pending_external_review"
    assert current["v114_3m_search_executed"] is True and current["v114_completed_route_count"] == 128
    assert current["v114_checkpoint_resumable"] is True and current["new_reviewed_maximum_expansions"] == 6500000
    assert current["long_v115_resume_executed"] is True
    assert current["current_best_result"] == 5651892.274552992
    assert history["external_verification_claimed"] is True
    assert history["external_review_status"] == "passed"
    assert history["heavy_output_excluded_from_source_archive"] is True
    assert current["candidate_115_beam_correction"]["plan_sha256"] == "2a0c60b73eb1760174bb867d886a45fd36dac42b019dac9d93dd360b1a44cd90"
    assert history["actual_runner_extension_fixture_passed"] is True
    assert history["preflight_no_mutation_guards_passed"] is True
    assert history["reviewed_inventory_entry_digest_sha256"] == "0bb00535354717d05ae1761fe6522bcc5129cc598cc8aaf072843626a7d43f15"
    print("project_progress_beam_v115_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
