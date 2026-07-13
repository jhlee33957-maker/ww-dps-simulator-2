from __future__ import annotations

from beam_search_final_replay_reporting_smoke_test import _run_search

import tempfile
from pathlib import Path


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-reporting-") as output:
        result = _run_search(Path(output), 2000)
        summary = result["route_replay_summaries"][0]
    required = {
        "damage_by_character",
        "damage_by_character_and_source",
        "effective_damage_role_breakdown",
        "damage_by_action_id",
        "damage_by_category",
        "action_use_counts",
        "scheduled_damage",
        "route_comparison",
        "comparison_against_references",
        "metadata_model_space_mismatch_status",
        "active_build_profiles",
        "data_contract_hashes",
    }
    assert required <= set(summary)
    assert abs(summary["damage_by_character_sum"] - summary["total_damage"]) <= 1e-6
    assert abs(summary["effective_damage_role_breakdown"]["total_damage_delta"]) <= 1e-6
    assert summary["metadata_model_space_mismatch_status"] == "none_party_preset_replay_uses_project_model_space"
    print("beam_search_completed_route_reporting_contract_smoke_test ok")


if __name__ == "__main__":
    main()
