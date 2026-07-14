from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    review = json.loads((ROOT / "results/beam_search_v114_3m_checkpoint_review_v115.json").read_text(encoding="utf-8"))
    assert review["expansions"] == 3000000
    assert review["completed_route_count"] == 0
    assert review["best_partial"]["interpretation"] == "diagnostic_only_not_a_winner_or_final_dps_result"
    assert review["status"] == "healthy_resumable_expansion_budget_exhausted"
    assert review["current_project_winner"]["total_damage"] == 5276844.358692044
    assert review["budget_projection"]["reviewed_resume_target"] == 6500000
    assert review["global_optimum_proven"] is False and review["heavy_checkpoint_excluded_from_candidate_archive"] is True
    print("beam_search_v114_3m_checkpoint_review_smoke_test ok")


if __name__ == "__main__":
    main()
