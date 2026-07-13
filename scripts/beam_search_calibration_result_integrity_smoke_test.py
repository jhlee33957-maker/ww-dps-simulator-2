from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "results" / "beam_search_v111"
PLAN = ROOT / "data" / "beam_search_plan_v111.json"

EXPECTED = {
    "plan_sha256": "b504def4e0c1da82ef2a6024d19ccac76fe175df51899e50d12f3bff99a17998",
    "bc_model_sha256": "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e",
    "prior_ppo_model_sha256": "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513",
    "manual_route_raw_sha256": "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a",
    "bc_npz_sha256": "b020a1b9309b46bd87eb3fff4837aead53035c4c84620962f47feb9fc11846ff",
    "action_data_hash": "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1",
    "party_config_hash": "bd106ba1c0f5581436c35fea736a00fd6ad92b131f8b43ba8cf1e3dc89cbcb11",
    "direct_action_manifest_sha256": "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d",
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _close(actual: float, expected: float) -> None:
    assert abs(float(actual) - expected) <= 1e-9, (actual, expected)


def _assert_portable_paths() -> None:
    forbidden = re.compile(r"(?:[A-Za-z]:[\\/]|(?:^|[\"'])/(?:tmp|var|home)/)")
    for path in RESULT_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".csv", ".log", ".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert not forbidden.search(text), f"machine-specific absolute path in {path.relative_to(ROOT)}"
        if path.suffix.lower() == ".json":
            json.loads(text)
        elif path.suffix.lower() == ".csv":
            list(csv.reader(text.splitlines()))


def main() -> None:
    result = _read_json(RESULT_ROOT / "execution_result.json")
    state = _read_json(RESULT_ROOT / "search_state.json")
    summary = _read_json(RESULT_ROOT / "calibration_result_summary.json")
    final_summary = _read_json(RESULT_ROOT / "final_summary.json")
    route = result["best_completed_search_route"]
    replay = result["route_replay_summaries"][0]

    assert hashlib.sha256(PLAN.read_bytes()).hexdigest() == EXPECTED["plan_sha256"]
    assert result["plan_path"] == "data/beam_search_plan_v111.json"
    assert result["plan_sha256"] == EXPECTED["plan_sha256"]
    assert result["output_root"] == "results/beam_search_v111"
    assert result["stage_id"] == "calibration_30s"
    assert result["status"] == result["termination_status"] == "completed_search"
    assert result["maximum_expansions"] == 500000
    assert result["expansions"] == 381918
    assert result["pending_buckets"] == [] and result["destination_bucket_accumulators"] == {}
    assert state["pending_buckets"] == [] and state["destination_bucket_accumulators"] == {}
    assert len(result["completed_buckets"]) == 60
    assert result["completed_route_count"] == 128
    assert result["next_completion_order"] == 12907
    assert result["checkpoint_count"] == 5
    assert result["frontier_file_write_count"] == 17
    assert result["accumulator_finalization_count"] == 18
    assert result["zero_time_expansion_count"] == 4605
    assert result["deduplicated_states"] == 17452 and result["pruned_states"] == 287717
    assert result["peak_live_nodes"] == 4234 and result["peak_serialized_payload_bytes"] == 29382
    assert result["tracked_memory_estimate"]["conservative_total_bytes"] == 253071736
    _close(result["elapsed_seconds"], 923.3255433000159)
    _close(result["expansions_per_second"], 413.6330926522451)

    assert route["route_id"] == "a301f753b3ddf6e4" and route["completion_order"] == 6908
    _close(route["total_damage"], 1369674.294344379)
    _close(route["dps"], 45655.8098114793)
    _close(route["combat_time"], 30.0)
    assert route["action_count"] == 45
    assert route["selected_sequence_sha256"] == "a301f753b3ddf6e47acc5aa4b3325ac2465f36db102974fc72bcedb64af82011"
    assert route["resolved_sequence_sha256"] == "d476c49e7aeba150d11fee9b23ccbc9047f5a4f8c8a5c462f6f9265423702fd5"
    assert replay["route_id"] == route["route_id"]
    for key in ("total_damage", "dps"):
        _close(replay[key], route[key])
    assert replay["selected_action_count"] == replay["resolved_action_count"] == route["action_count"]
    assert replay["selected_sequence_sha256"] == route["selected_sequence_sha256"]
    assert replay["resolved_sequence_sha256"] == route["resolved_sequence_sha256"]
    _close(replay["final_combat_time"], route["combat_time"])
    _close(replay["damage_by_character_sum"], route["total_damage"])
    _close(replay["effective_damage_role_breakdown"]["total_damage_delta"], 0.0)
    _close(replay["scheduled_damage"], 56004.767902583255)
    _close(replay["effective_damage_role_breakdown"]["generated_mechanic_damage"], 123343.33773087071)
    assert replay["reference_damage_comparison_status"] == "horizon_mismatch_not_comparable"
    assert replay["comparison_against_references"]["numeric_total_damage_ranking"] is None
    assert final_summary["winner"] is None and final_summary["calibration_only_no_project_winner"] is True
    assert final_summary["global_optimum_proven"] is False
    assert summary["reference_damage_comparison_status"] == "horizon_mismatch_not_comparable"
    assert summary["calibration_only_no_project_winner"] is True
    assert summary["immutable_hashes"] == {
        key: value for key, value in EXPECTED.items() if key != "plan_sha256"
    }
    assert not any(path.is_file() for path in (RESULT_ROOT / "frontier").rglob("*"))
    canonical_paths = summary["canonical_paths"]
    assert canonical_paths["replay_summary"] == "results/beam_search_v111/routes/a301f753b3ddf6e4_summary.json"
    assert canonical_paths["replay_timeline"] == "results/beam_search_v111/routes/a301f753b3ddf6e4_timeline.csv"
    for path_text in canonical_paths.values():
        assert (ROOT / path_text).exists(), path_text
    _assert_portable_paths()
    print("beam_search_calibration_result_integrity_smoke_test ok")


if __name__ == "__main__":
    main()
