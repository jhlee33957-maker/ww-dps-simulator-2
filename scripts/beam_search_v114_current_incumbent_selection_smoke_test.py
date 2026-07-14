from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import V115_RESUME_V114_PLAN_PATH, load_plan
from search.beam_reporting import load_project_comparison_incumbent, select_damage_only_winner


def main() -> None:
    plan = load_plan(V115_RESUME_V114_PLAN_PATH)
    incumbent = load_project_comparison_incumbent(plan)
    assert incumbent["model_sha256"] == "dc437ff4e03b50001e9829550b1e52ff0f503d963ec3433a7adf88848b5e3073"
    assert incumbent["total_damage"] == 5276844.358692044
    assert incumbent["selected_sequence_sha256"] == "27920c26c93bc51aacb964211062b301a2af16b899e2bbafc442edca17e72c54"
    assert incumbent["resolved_sequence_sha256"] == "350df3b0df184b5d9e8c5cecffef7893ddb53f6d31eeaf864bf7c61fb71590f0"
    for damage in (5100000.0, 5200000.0, 5276844.358692044):
        winner = select_damage_only_winner([{"winner_kind": "beam_search_route", "total_damage": damage}], incumbent=incumbent)
        assert winner["winner_kind"] == "reviewed_v114_model"
    assert select_damage_only_winner([{"winner_kind": "beam_search_route", "total_damage": 5280000.0}], incumbent=incumbent)["winner_kind"] == "beam_search_route"
    for key in ("result_sha256", "model_sha256", "total_damage", "selected_sequence_sha256"):
        bad = copy.deepcopy(plan)
        bad["comparison_incumbent_contract"][key] = "0" * 64 if "sha256" in key else 1.0
        try:
            load_project_comparison_incumbent(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"mutation accepted: {key}")
    print("beam_search_v114_current_incumbent_selection_smoke_test ok")


if __name__ == "__main__":
    main()
