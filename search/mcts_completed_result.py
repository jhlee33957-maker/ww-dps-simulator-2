from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any

from search.mcts_reporting import replay_completed_route


RAW_RESULT = Path("results/mcts_v117_32gb/calibration_20k_seed_117001")
COMPACT_RESULT = Path("results/mcts_v117_calibration_20k_v118")
PLAN_PATH = Path("data/mcts_plan_v117_32gb.json")
REVIEW_ARCHIVE = Path("mcts_v117_20k_review.zip")
REVIEW_ARCHIVE_SHA256 = "71af1ed95f574c4fc28284e3b77f8bf944828571d1dd3bce3a7dc746a2c78fb3"
REVIEW_INVENTORY_SHA256 = "e9b2476d28d4f6fe9c1aaad6eb35900710dab3ca6e85088085a5e3bd69fb5818"
INVENTORY_ENTRY_DIGEST = "b959d86ca0e4657e6dd918340eef87a520b02ea158bb30f661928f81b204e0b7"
EXPECTED_FILE_COUNT = 111
EXPECTED_TOTAL_BYTES = 38_944_560
PLAN_SHA256 = "4d69880283f7a2fe837631fece76cd5eb06e62af544b31e9ea6c96f1a82f11bb"
WINNER_ID = "5aab329ce5b526a7"
WINNER_DAMAGE = 4_128_137.812582737
WINNER_DPS = 34_401.14843818948
WINNER_SELECTED_SHA = "5aab329ce5b526a709d530ae0a3037d4e8e776dff7726bfa0ecc4b02ca83116c"
WINNER_RESOLVED_SHA = "bccd12d7c852d65e168e4ead82fd6fb2514d4d856e865db41a74620699316e1d"
BEAM_DAMAGE = 5_651_892.274552992
MODEL_DAMAGE = 5_276_844.358692044
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

CORE_HASHES = {
    "execution_result.json": "457ea3d8d5ef7a0b38f8cb173048b60f532544ce25b1356b296991da86c08ed0",
    "final_summary.json": "dedfbaefd5fcea9f266b98a286b2a7fb575c96907a2ca7e351560b220c1b94f6",
    "leaderboard.json": "4f9cb6dc87ab90374cd5b390dd19eb11bafb8a518d201e562ad5b5af2d2650ac",
    "completed_routes_compact.json": "4f9cb6dc87ab90374cd5b390dd19eb11bafb8a518d201e562ad5b5af2d2650ac",
    "best_route.json": "05406a3f6b4e4e4ddb25c5c307f07bc9bc0f9d85795df6b3d445864f070ae997",
    f"routes/{WINNER_ID}_summary.json": "a5aec0cef09f038ec2b8322227473fe62c3dc54efb0f677fce2dd3b06d2adcf1",
    f"routes/{WINNER_ID}_timeline.csv": "22c5325535a55352b590fcb234683f25437f4d72a9ff3c6adf8a50b34d8c5e55",
    "checkpoint/latest_manifest.json": "0c6aa76f70abed351f96458c5cec6bec8add30592e600c322e78b0700d44b485",
    "checkpoint/previous_manifest.json": "1c52255d2ebc568a2480eebe56ad8994709ca9dab1ef152e9f4e753a1feec09f",
}

PROGRESSION = [
    (1000, 2_923_979.8335301215), (2000, 3_184_203.7336018938),
    (3000, 3_498_929.9226562413), (4000, 3_764_027.8197907014),
    (5000, 3_916_158.19797584), (8000, 4_123_783.6584580713),
    (12000, WINNER_DAMAGE), (20000, WINNER_DAMAGE),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = [{"path": str(row["path"]).replace("\\", "/"), "bytes": int(row["bytes"]),
               "sha256": str(row["sha256"]).lower()} for row in entries]
    result.sort(key=lambda row: row["path"])
    return result


def _validate_inventory_payload(payload: dict[str, Any], *, source: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("files"), list):
        raise ValueError(f"{source} inventory payload is malformed")
    entries = normalize_entries(payload["files"])
    if len(entries) != EXPECTED_FILE_COUNT or int(payload.get("file_count", -1)) != EXPECTED_FILE_COUNT:
        raise ValueError(f"{source} inventory file count mismatch")
    if int(payload.get("total_bytes", -1)) != EXPECTED_TOTAL_BYTES or sum(row["bytes"] for row in entries) != EXPECTED_TOTAL_BYTES:
        raise ValueError(f"{source} inventory byte count mismatch")
    if len({row["path"] for row in entries}) != len(entries):
        raise ValueError(f"{source} inventory contains duplicate paths")
    for row in entries:
        path = Path(row["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe {source} inventory path: {row['path']}")
        if row["bytes"] < 0 or SHA256_PATTERN.fullmatch(row["sha256"]) is None:
            raise ValueError(f"Invalid {source} inventory entry: {row['path']}")
    if entry_digest(entries) != INVENTORY_ENTRY_DIGEST:
        raise ValueError(f"{source} inventory normalized digest mismatch")
    return dict(payload) | {"files": entries, "inventory_file_sha256": REVIEW_INVENTORY_SHA256,
                            "normalized_entry_digest_sha256": INVENTORY_ENTRY_DIGEST}


def entry_digest(entries: list[dict[str, Any]]) -> str:
    normalized = normalize_entries(entries)
    raw = json.dumps(
        [[row["path"], row["bytes"], row["sha256"]] for row in normalized],
        separators=(",", ":"), ensure_ascii=False,
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def load_review_inventory(project_root: Path) -> dict[str, Any]:
    """Load external review evidence. This is intentionally ingestion-only."""
    archive_path = project_root / REVIEW_ARCHIVE
    if sha256_file(archive_path) != REVIEW_ARCHIVE_SHA256:
        raise ValueError("MCTS review archive SHA-256 mismatch")
    with zipfile.ZipFile(archive_path) as archive:
        if len(archive.infolist()) != 74 or archive.testzip() is not None:
            raise ValueError("MCTS review archive structure/CRC mismatch")
        raw = archive.read("FULL_RESULT_FILE_INVENTORY.json")
        if hashlib.sha256(raw).hexdigest() != REVIEW_INVENTORY_SHA256:
            raise ValueError("MCTS reviewed inventory SHA-256 mismatch")
    return _validate_inventory_payload(json.loads(raw), source="reviewed")


def load_compact_review_inventory(project_root: Path) -> dict[str, Any]:
    """Load the packaged, self-contained authority used by validation and cleanup."""
    compact = project_root.resolve() / COMPACT_RESULT
    manifest_path = compact / "result_manifest.json"
    manifest = _load(manifest_path)
    if manifest.get("schema_version") != "mcts_v117_calibration_result_manifest_v118":
        raise ValueError("MCTS compact result manifest schema mismatch")
    exact_manifest = {
        "ingestion_candidate": 118,
        "source_raw_output_path": RAW_RESULT.as_posix(),
        "calibration_only": True,
        "production_mcts_executed": False,
        "global_optimum_proven": False,
    }
    for key, expected in exact_manifest.items():
        if manifest.get(key) != expected:
            raise ValueError(f"MCTS compact result manifest {key} mismatch")
    calibration = manifest.get("calibration") or {}
    exact_calibration = {
        "algorithm": "state_uct_mast_v117", "stage": "calibration_20k_seed_117001", "seed": 117001,
        "simulations": 20000, "completed_rollouts": 20000, "invalid_rollouts": 0,
        "node_count": 20001, "retained_routes": 128,
    }
    for key, expected in exact_calibration.items():
        if calibration.get(key) != expected:
            raise ValueError(f"MCTS compact calibration {key} mismatch")
    winner = calibration.get("winner") or {}
    winner_exact = {"route_id": WINNER_ID, "total_damage": WINNER_DAMAGE, "dps": WINNER_DPS,
                    "selected_sequence_sha256": WINNER_SELECTED_SHA, "resolved_sequence_sha256": WINNER_RESOLVED_SHA}
    for key, expected in winner_exact.items():
        if winner.get(key) != expected:
            raise ValueError(f"MCTS compact winner {key} mismatch")
    full_inventory = manifest.get("full_inventory") or {}
    inventory_exact = {"file_count": EXPECTED_FILE_COUNT, "total_bytes": EXPECTED_TOTAL_BYTES,
                       "inventory_file_sha256": REVIEW_INVENTORY_SHA256,
                       "normalized_entry_digest_sha256": INVENTORY_ENTRY_DIGEST}
    for key, expected in inventory_exact.items():
        if full_inventory.get(key) != expected:
            raise ValueError(f"MCTS compact manifest inventory {key} mismatch")
    expected_artifact_sha = (manifest.get("artifact_sha256") or {}).get("full_result_inventory.json")
    if SHA256_PATTERN.fullmatch(str(expected_artifact_sha)) is None:
        raise ValueError("MCTS compact manifest inventory artifact SHA is invalid")
    inventory_path = compact / "full_result_inventory.json"
    if sha256_file(inventory_path) != expected_artifact_sha:
        raise ValueError("MCTS compact full-result inventory artifact SHA mismatch")
    payload = _load(inventory_path)
    if payload.get("schema_version") != "mcts_v117_full_result_inventory_v118":
        raise ValueError("MCTS compact full-result inventory schema mismatch")
    if payload.get("result_root") != RAW_RESULT.as_posix():
        raise ValueError("MCTS compact full-result inventory root mismatch")
    if payload.get("reviewed_inventory_file_sha256") != REVIEW_INVENTORY_SHA256:
        raise ValueError("MCTS compact reviewed inventory source SHA mismatch")
    if payload.get("normalized_entry_digest_sha256") != INVENTORY_ENTRY_DIGEST:
        raise ValueError("MCTS compact inventory declared digest mismatch")
    validated = _validate_inventory_payload(payload, source="compact")
    return validated | {"result_manifest": manifest, "artifact_sha256": expected_artifact_sha}


def validate_inventory(output_root: Path, inventory: dict[str, Any]) -> dict[str, Any]:
    expected = {row["path"]: row for row in inventory["files"]}
    actual = sorted(p.relative_to(output_root).as_posix() for p in output_root.rglob("*") if p.is_file())
    if set(actual) != set(expected):
        raise ValueError(f"MCTS raw inventory paths mismatch: missing={sorted(set(expected)-set(actual))[:5]} added={sorted(set(actual)-set(expected))[:5]}")
    for relative in actual:
        path = output_root / relative
        row = expected[relative]
        if path.stat().st_size != row["bytes"] or sha256_file(path) != row["sha256"]:
            raise ValueError(f"MCTS raw inventory mismatch: {relative}")
    return {"file_count": len(actual), "total_bytes": sum(expected[p]["bytes"] for p in actual),
            "normalized_entry_digest_sha256": entry_digest(list(expected.values()))}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_calibration(project_root: Path, output_root: Path, *, replay: bool = True,
                         inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    project_root = project_root.resolve(); output_root = output_root.resolve()
    inventory = inventory or load_compact_review_inventory(project_root)
    inventory_result = validate_inventory(output_root, inventory)
    for relative, expected in CORE_HASHES.items():
        if sha256_file(output_root / relative) != expected:
            raise ValueError(f"MCTS reviewed core hash mismatch: {relative}")
    if sha256_file(project_root / PLAN_PATH) != PLAN_SHA256:
        raise ValueError("MCTS candidate-117 plan hash mismatch")
    execution = _load(output_root / "execution_result.json")
    leaderboard = _load(output_root / "leaderboard.json")
    source_summary = _load(output_root / f"routes/{WINNER_ID}_summary.json")
    latest = _load(output_root / "checkpoint/latest_manifest.json")
    previous = _load(output_root / "checkpoint/previous_manifest.json")
    exact = {"algorithm": "state_uct_mast_v117", "stage_id": "calibration_20k_seed_117001", "seed": 117001,
             "termination_status": "simulation_budget_exhausted", "simulations_requested": 20000,
             "simulations_completed": 20000, "completed_rollout_count": 20000, "invalid_rollout_count": 0,
             "node_count": 20001, "normal_process_exit": True, "global_optimum_proven": False}
    for key, expected in exact.items():
        if execution.get(key) != expected:
            raise ValueError(f"MCTS calibration {key} mismatch")
    if latest.get("simulation_count") != 20000 or latest.get("node_count") != 20001:
        raise ValueError("MCTS latest checkpoint count mismatch")
    if previous.get("simulation_count") != 19000 or previous.get("node_count") != 19001:
        raise ValueError("MCTS previous checkpoint count mismatch")
    for manifest in (latest, previous):
        if manifest.get("plan_sha256") != PLAN_SHA256:
            raise ValueError("MCTS checkpoint plan SHA mismatch")
        for entry in manifest.get("files", {}).values():
            path = output_root / "checkpoint" / entry["path"]
            if path.stat().st_size != int(entry["bytes"]) or sha256_file(path) != entry["sha256"]:
                raise ValueError(f"MCTS checkpoint payload mismatch: {entry['path']}")
    routes = list(leaderboard.get("routes", []))
    if len(routes) != 128 or leaderboard.get("retained_route_count") != 128:
        raise ValueError("MCTS retained-route count mismatch")
    if any(float(route["combat_time"]) != 120.0 for route in routes):
        raise ValueError("MCTS retained route is not a completed 120-second route")
    ordering = [(float(r["total_damage"]), r["selected_sequence_sha256"]) for r in routes]
    if ordering != sorted(ordering, key=lambda item: (-item[0], item[1])):
        raise ValueError("MCTS leaderboard ordering mismatch")
    winner = leaderboard["winner"]
    winner_exact = {"route_id": WINNER_ID, "total_damage": WINNER_DAMAGE, "dps": WINNER_DPS,
                    "combat_time": 120.0, "action_count": 180, "selected_sequence_sha256": WINNER_SELECTED_SHA,
                    "resolved_sequence_sha256": WINNER_RESOLVED_SHA, "completion_simulation_index": 11561}
    for key, expected in winner_exact.items():
        if winner.get(key) != expected:
            raise ValueError(f"MCTS winner {key} mismatch")
    if winner != routes[0] or max(float(r["total_damage"]) for r in routes) != WINNER_DAMAGE:
        raise ValueError("MCTS winner is not the maximum retained route")
    expected_summary = {"selected_action_count": 180, "resolved_action_count": 180, "executed_action_count": 180,
                        "final_combat_time": 120.0, "total_damage": WINNER_DAMAGE,
                        "selected_sequence_sha256": WINNER_SELECTED_SHA, "resolved_sequence_sha256": WINNER_RESOLVED_SHA}
    for key, expected in expected_summary.items():
        if source_summary.get(key) != expected:
            raise ValueError(f"MCTS winning summary {key} mismatch")
    if not all(row["available_before_execution"] and row["executed"] for row in source_summary["attempted_actions"]):
        raise ValueError("MCTS winning source replay contains unavailable/failed action")
    with (output_root / f"routes/{WINNER_ID}_timeline.csv").open("r", encoding="utf-8", newline="") as file:
        timeline = list(csv.DictReader(file))
    if len(timeline) != 180 or abs(sum(float(r["damage"]) for r in timeline) - WINNER_DAMAGE) > 1e-6:
        raise ValueError("MCTS winning timeline damage/count mismatch")
    truncated = [r for r in timeline if r["truncated_by_combat_limit"].lower() == "true"]
    if len(truncated) != 1 or truncated[0]["resolved_action_id"] != "lynae_visual_impact" or float(truncated[0]["combat_time_start"]) != 119.91666666666664:
        raise ValueError("MCTS winning horizon truncation mismatch")
    replay_summary = source_summary
    if replay:
        replay_summary = replay_completed_route(winner)
        if replay_summary["resolved_sequence_sha256"] != WINNER_RESOLVED_SHA:
            raise ValueError("MCTS winning normal replay hash mismatch")
    return {"inventory": inventory, "inventory_validation": inventory_result, "execution": execution,
            "leaderboard": leaderboard, "winner": winner, "source_summary": source_summary,
            "replay_summary": replay_summary, "latest_manifest": latest, "previous_manifest": previous,
            "timeline": timeline}


def corrected_metrics(execution: dict[str, Any]) -> dict[str, Any]:
    raw = dict(execution["phase_seconds"])
    exclusive_selection = raw["selection"] - raw["expansion"]
    exclusive = {"selection": exclusive_selection, "expansion": raw["expansion"], "rollout": raw["rollout"],
                 "backpropagation": raw["backpropagation"], "checkpoint": raw["checkpoint"]}
    phase_sum = sum(exclusive.values())
    elapsed = float(execution["elapsed_seconds"])
    return {"schema_version": "mcts_corrected_execution_metrics_v118",
            "source_execution_result_sha256": CORE_HASHES["execution_result.json"],
            "source_phase_fields_status": "historical_overlapping_selection_includes_expansion",
            "raw_inclusive_phase_seconds": raw, "exclusive_phase_seconds": exclusive,
            "exclusive_phase_sum_seconds": phase_sum, "other_overhead_seconds": elapsed - phase_sum,
            "elapsed_seconds": elapsed, "phase_sum_within_elapsed": phase_sum <= elapsed + 1e-6,
            "correction_affects_search_state": False}


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def build_compact_artifacts(project_root: Path, output_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve(); output_root = output_root.resolve()
    reviewed_inventory = load_review_inventory(project_root)
    before = validate_calibration(project_root, output_root, replay=True, inventory=reviewed_inventory)
    compact = project_root / COMPACT_RESULT
    inventory_payload = {"schema_version": "mcts_v117_full_result_inventory_v118", "result_root": RAW_RESULT.as_posix(),
                         "file_count": EXPECTED_FILE_COUNT, "total_bytes": EXPECTED_TOTAL_BYTES,
                         "reviewed_inventory_file_sha256": REVIEW_INVENTORY_SHA256,
                         "normalized_entry_digest_sha256": INVENTORY_ENTRY_DIGEST,
                         "files": before["inventory"]["files"]}
    _atomic_json(compact / "full_result_inventory.json", inventory_payload)
    metrics = corrected_metrics(before["execution"]); _atomic_json(compact / "corrected_execution_metrics.json", metrics)
    progression = {"schema_version": "mcts_best_damage_progression_v118",
                   "checkpoints": [{"simulation": s, "best_damage": d} for s, d in PROGRESSION],
                   "final_best_first_found_simulation": 11561, "simulations_without_improvement_after_best": 8439,
                   "plateau_interpretation": "calibration_observation_not_optimum_proof", "global_optimum_proven": False}
    _atomic_json(compact / "best_damage_progression.json", progression)
    compact_routes = [{k: v for k, v in route.items() if k != "selected_sequence"} for route in before["leaderboard"]["routes"]]
    leaderboard = {"schema_version": "mcts_v117_calibration_leaderboard_v118", "calibration_only": True,
                   "retained_route_count": 128, "sort": "damage_desc_then_selected_sha_asc",
                   "routes": compact_routes, "winner": compact_routes[0], "global_optimum_proven": False}
    _atomic_json(compact / "leaderboard.json", leaderboard)
    best_route = {"schema_version": "mcts_v117_calibration_best_route_v118", "winner": before["winner"],
                  "calibration_only": True, "global_optimum_proven": False}
    _atomic_json(compact / "best_route.json", best_route)
    _atomic_json(compact / "winning_route_summary.json", before["source_summary"])
    (compact / "winning_route_timeline.csv").write_bytes((output_root / f"routes/{WINNER_ID}_timeline.csv").read_bytes())
    checkpoint_summary = {"schema_version": "mcts_checkpoint_manifest_summary_v118",
                          "latest_manifest_sha256": CORE_HASHES["checkpoint/latest_manifest.json"],
                          "previous_manifest_sha256": CORE_HASHES["checkpoint/previous_manifest.json"],
                          "latest": {k: before["latest_manifest"][k] for k in ("simulation_count", "node_count", "completed_route_count", "best_completed_route")},
                          "previous": {k: before["previous_manifest"][k] for k in ("simulation_count", "node_count", "completed_route_count", "best_completed_route")},
                          "raw_checkpoint_payload_preserved_locally": True}
    _atomic_json(compact / "checkpoint_manifest_summary.json", checkpoint_summary)
    comparisons = {"beam": {"damage": BEAM_DAMAGE, "delta": WINNER_DAMAGE - BEAM_DAMAGE,
                             "relative_percent": (WINNER_DAMAGE / BEAM_DAMAGE - 1.0) * 100.0},
                   "best_trained_model": {"damage": MODEL_DAMAGE, "delta": WINNER_DAMAGE - MODEL_DAMAGE,
                                          "relative_percent": (WINNER_DAMAGE / MODEL_DAMAGE - 1.0) * 100.0}}
    final = {"schema_version": "mcts_v117_calibration_final_summary_v118", "termination_status": "simulation_budget_exhausted",
             "simulations_completed": 20000, "completed_rollouts": 20000, "invalid_rollouts": 0,
             "winner": compact_routes[0], "comparisons": comparisons, "calibration_only": True,
             "production_mcts_executed": False, "current_overall_winner": "completed_beam_route_67a4250b3b8d0de9",
             "global_optimum_proven": False}
    _atomic_json(compact / "final_summary.json", final)
    artifacts = ["final_summary.json", "leaderboard.json", "best_route.json", "winning_route_summary.json",
                 "winning_route_timeline.csv", "corrected_execution_metrics.json", "best_damage_progression.json",
                 "full_result_inventory.json", "checkpoint_manifest_summary.json"]
    after = validate_inventory(output_root, before["inventory"])
    manifest = {"schema_version": "mcts_v117_calibration_result_manifest_v118", "ingestion_candidate": 118,
                "source_raw_output_path": RAW_RESULT.as_posix(), "raw_output_preserved_locally": True,
                "review_archive": {"path": REVIEW_ARCHIVE.as_posix(), "sha256": REVIEW_ARCHIVE_SHA256, "entries": 74},
                "full_inventory": {"file_count": EXPECTED_FILE_COUNT, "total_bytes": EXPECTED_TOTAL_BYTES,
                                   "inventory_file_sha256": REVIEW_INVENTORY_SHA256,
                                   "normalized_entry_digest_sha256": INVENTORY_ENTRY_DIGEST,
                                   "before_validation": before["inventory_validation"], "after_validation": after},
                "reviewed_core_hashes": CORE_HASHES, "plan": {"path": PLAN_PATH.as_posix(), "sha256": PLAN_SHA256},
                "calibration": {"algorithm": "state_uct_mast_v117", "stage": "calibration_20k_seed_117001", "seed": 117001,
                                "simulations": 20000, "completed_rollouts": 20000, "invalid_rollouts": 0, "node_count": 20001,
                                "retained_routes": 128, "winner": compact_routes[0]},
                "comparisons": comparisons, "plateau": progression, "phase_time_correction": metrics,
                "artifact_sha256": {name: sha256_file(compact / name) for name in artifacts},
                "calibration_only": True, "production_mcts_executed": False, "global_optimum_proven": False}
    _atomic_json(compact / "result_manifest.json", manifest)
    return {"status": "compact_calibration_artifacts_written", "compact_root": compact.as_posix(),
            "manifest_sha256": sha256_file(compact / "result_manifest.json"), "raw_inventory_before": before["inventory_validation"],
            "raw_inventory_after": after, "winning_route_id": WINNER_ID, "winning_damage": WINNER_DAMAGE}
