from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from search.mcts_production_result import COMPACT_RESULT, SEEDS
from search.mcts_reporting import replay_completed_route
from search.search_state_codec import sequence_sha256


ARTIFACT_NAMES = (
    "best_route.json",
    "winning_route_summary.json",
    "winning_route_timeline.csv",
    "final_summary.json",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_seed_artifacts(seed: int) -> dict[str, bytes]:
    seed_dir = ROOT / COMPACT_RESULT / f"seed_{seed}"
    return {name: (seed_dir / name).read_bytes() for name in ARTIFACT_NAMES}


def _expected_artifact_hashes(seed: int) -> dict[str, str]:
    expected = SEEDS[seed]
    route_id = expected["route_id"]
    core_hashes = expected["core_hashes"]
    return {
        "best_route.json": core_hashes["best_route.json"],
        "winning_route_summary.json": core_hashes[f"routes/{route_id}_summary.json"],
        "winning_route_timeline.csv": core_hashes[f"routes/{route_id}_timeline.csv"],
    }


def validate_seed_artifacts(seed: int, artifacts: dict[str, bytes]) -> dict[str, Any]:
    expected = SEEDS[seed]
    assert set(artifacts) == set(ARTIFACT_NAMES)
    for name, expected_hash in _expected_artifact_hashes(seed).items():
        assert _sha256(artifacts[name]) == expected_hash, (seed, name)

    best_route = json.loads(artifacts["best_route.json"].decode("utf-8"))
    winner = best_route["winner"]
    winner_contract = {
        "route_id": expected["route_id"],
        "total_damage": expected["damage"],
        "dps": expected["dps"],
        "combat_time": 120.0,
        "current_time": expected["current_time"],
        "action_count": expected["actions"],
        "selected_sequence_sha256": expected["selected_sha"],
        "resolved_sequence_sha256": expected["resolved_sha"],
        "completion_simulation_index": expected["completion_simulation"],
    }
    for key, value in winner_contract.items():
        assert winner[key] == value, (seed, key)
    assert len(winner["selected_sequence"]) == expected["actions"]
    assert sequence_sha256(winner["selected_sequence"]) == expected["selected_sha"]

    summary = json.loads(artifacts["winning_route_summary.json"].decode("utf-8"))
    assert summary["route_id"] == expected["route_id"]
    assert summary["selected_action_count"] == expected["actions"]
    assert summary["resolved_action_count"] == expected["actions"]
    assert summary["executed_action_count"] == expected["actions"]
    assert summary["selected_sequence_sha256"] == expected["selected_sha"]
    assert summary["resolved_sequence_sha256"] == expected["resolved_sha"]
    assert summary["total_damage"] == expected["damage"]
    assert summary["final_combat_time"] == 120.0
    attempts = summary["attempted_actions"]
    assert len(attempts) == expected["actions"]
    assert all(row["available_before_execution"] is True and row["executed"] is True for row in attempts)
    assert sequence_sha256([row["selected_action_id"] for row in attempts]) == expected["selected_sha"]
    assert sequence_sha256([row["resolved_action_id"] for row in attempts]) == expected["resolved_sha"]

    timeline = list(csv.DictReader(io.StringIO(artifacts["winning_route_timeline.csv"].decode("utf-8"))))
    assert len(timeline) == expected["actions"]
    assert [row["selected_action_id"] for row in timeline] == [row["selected_action_id"] for row in attempts]
    assert [row["resolved_action_id"] for row in timeline] == [row["resolved_action_id"] for row in attempts]
    assert sum(float(row["damage"]) for row in timeline) == summary["timeline_damage_sum"]

    final_summary = json.loads(artifacts["final_summary.json"].decode("utf-8"))
    assert final_summary["seed"] == seed
    assert final_summary["stage_id"] == expected["stage_id"]
    assert final_summary["production_search_result"] is True
    assert final_summary["winner"] == winner

    if seed == 118003:
        assert summary["timeline_damage_sum"] == 4647724.703247971
        assert summary["total_damage"] == 4647724.703247974
        truncated = [row for row in timeline if row["truncated_by_combat_limit"].lower() == "true"]
        assert len(truncated) == 1
        assert truncated[0]["resolved_action_id"] == "aemeath_basic_form_stage_2"
        assert float(truncated[0]["damage"]) == 0.0

    return {"winner": winner, "summary": summary, "timeline": timeline}


def validate_replay_policy(progress: dict[str, Any], *, replay_skipped: bool | None = None) -> bool:
    timing = progress["candidate_124_timing_core_1"]
    requires_rebaseline = timing.get("historical_results_status") == "preserved_but_requires_timing_rebaseline"
    if requires_rebaseline:
        assert timing["historical_result_files_rewritten"] is False
        assert timing["mornye_liberation_state_timing_implemented"] is True
    if replay_skipped is not None:
        assert replay_skipped is requires_rebaseline
    return requires_rebaseline


def _replace_json_value(payload: bytes, path: tuple[str, ...], value: Any) -> bytes:
    data = json.loads(payload.decode("utf-8"))
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def assert_mutations_rejected(progress: dict[str, Any], canonical: dict[int, dict[str, bytes]]) -> None:
    mutations: list[tuple[str, int, dict[str, bytes]]] = []

    changed_route_hash = dict(canonical[118001])
    changed_route_hash["best_route.json"] = _replace_json_value(
        changed_route_hash["best_route.json"],
        ("winner", "selected_sequence_sha256"),
        "0" * 64,
    )
    mutations.append(("stored route hash changed", 118001, changed_route_hash))

    changed_damage = dict(canonical[118002])
    changed_damage["winning_route_summary.json"] = _replace_json_value(
        changed_damage["winning_route_summary.json"],
        ("total_damage",),
        SEEDS[118002]["damage"] + 1.0,
    )
    mutations.append(("stored damage changed", 118002, changed_damage))

    changed_summary = dict(canonical[118003])
    changed_summary["winning_route_summary.json"] += b" "
    mutations.append(("stored summary changed", 118003, changed_summary))

    changed_timeline = dict(canonical[118003])
    changed_timeline["winning_route_timeline.csv"] += b"\n"
    mutations.append(("stored timeline changed", 118003, changed_timeline))

    for label, seed, artifacts in mutations:
        try:
            validate_seed_artifacts(seed, artifacts)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"historical artifact guard accepted mutation: {label}")

    rewritten = deepcopy(progress)
    rewritten["candidate_124_timing_core_1"]["historical_result_files_rewritten"] = True
    try:
        validate_replay_policy(rewritten, replay_skipped=True)
    except AssertionError:
        pass
    else:
        raise AssertionError("replay policy accepted historical_result_files_rewritten=true")

    missing_status = deepcopy(progress)
    missing_status["candidate_124_timing_core_1"].pop("historical_results_status")
    try:
        validate_replay_policy(missing_status, replay_skipped=True)
    except AssertionError:
        pass
    else:
        raise AssertionError("replay policy skipped replay without timing-rebaseline status")


def main() -> None:
    canonical = {seed: _load_seed_artifacts(seed) for seed in SEEDS}
    validated = {seed: validate_seed_artifacts(seed, artifacts) for seed, artifacts in canonical.items()}
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    skip_replay = validate_replay_policy(progress)
    assert_mutations_rejected(progress, canonical)

    if not skip_replay:
        for seed, expected in SEEDS.items():
            replay = replay_completed_route(validated[seed]["winner"])
            assert replay["selected_action_count"] == expected["actions"]
            assert replay["resolved_action_count"] == expected["actions"]
            assert replay["executed_action_count"] == expected["actions"]
            assert replay["selected_sequence_sha256"] == expected["selected_sha"]
            assert replay["resolved_sequence_sha256"] == expected["resolved_sha"]
            assert replay["total_damage"] == expected["damage"]
            assert replay["final_combat_time"] == 120.0

    print(
        "mcts_v118_3x50k_winner_replay_parity_smoke_test ok "
        f"historical_artifacts_preserved={str(skip_replay).lower()} "
        f"timing_rebaseline_required={str(skip_replay).lower()} winners={len(validated)}"
    )


if __name__ == "__main__":
    main()
