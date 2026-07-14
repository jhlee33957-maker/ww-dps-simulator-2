from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from rl.demo_contract import action_data_hash, party_config_hash
from search.beam_performance import performance_accounting
from search.beam_reporting import current_reference_comparisons, replay_selected_route_to_files


ROOT = Path(__file__).resolve().parents[1]
COMPLETED_DIR = Path("results/beam_search_v114_completed_v116")
COMPLETED_INVENTORY_PATH = Path("results/beam_search_v114_completed_inventory_v116.json")
HEAVY_OUTPUT = Path("results/beam_search_v114_lowmem_32gb")
PLAN_PATH = Path("data/beam_search_plan_v115_32gb_resume_v114.json")
PLAN_SHA256 = "2a0c60b73eb1760174bb867d886a45fd36dac42b019dac9d93dd360b1a44cd90"
REVIEW_ARCHIVE_SHA256 = "7479262e8074f9bb2fc972ed6f9dd0ccd35fdcba015d4f231a47458de4c91000"
REVIEW_INVENTORY_FILE_SHA256 = "b44dbbdcea36bdad138fd173922e4a92489d1bef0774cea49ade460ab35a1fed"
REVIEW_INVENTORY_ENTRY_DIGEST = "19e808db96952ea9405ed4d9699075073fbf61dcbc68a8b12e83acfa3b2ed854"
EXPECTED_FILE_COUNT = 1051
EXPECTED_TOTAL_BYTES = 2538957524
WINNER_ROUTE_ID = "67a4250b3b8d0de9"
WINNER_DAMAGE = 5651892.274552992
WINNER_DPS = 47099.1022879416
WINNER_SELECTED_SHA256 = "67a4250b3b8d0de9cec625448756226106ef0ed5134b8c4e4a0378518fa2f434"
WINNER_RESOLVED_SHA256 = "2b594e575203f29293b1f0e57ae51a07ff85d535ac957bde38a5911f6858c43a"
MODEL_DAMAGE = 5276844.358692044
MODEL_DPS = 43973.70298910037
MODEL_PATH = "models/guarded_ppo_v109/bc_conservative_seed_11/step_000090000.zip"
MODEL_SHA256 = "dc437ff4e03b50001e9829550b1e52ff0f503d963ec3433a7adf88848b5e3073"

CORE_HASHES = {
    "best_route.json": "5cfae9331498d7f02f60e4371c7582b0f1d9914d43dd253d8c9a68776b0e7bff",
    "execution_result.json": "a5e8500a7e65163b01ca58dcb88483829d515568ee8178824dd8fa282c67123a",
    "final_summary.json": "b42d51d24f4c60dd06249ee53272efd4820bda909c35a651a3ff5b8400f2f728",
    "leaderboard.json": "7fa78d6ebadc44b70682310add0add07c7a0cdb38a909b2636a139fb54ec5408",
    "search_state.json": "87ee9481c0eee7122e1a5ca30a4ee0b95bcc026260b5e977e52561c5cafb5794",
    "logs/full_120s_lowmem_32gb_v114.log": "7a966df6101ad7a45ae1034ef2205bd47a4b6f32b4814bc34d77a7e8fd31cd39",
    "routes/67a4250b3b8d0de9_summary.json": "9c5c5797ec28f2b15f2a8cef16d36e304f005cd155cf5a9584b2bfe11e571c36",
    "routes/67a4250b3b8d0de9_timeline.csv": "dfe6361d1901a93168bf54af45c9c8187b88959f15a4bb8b3f53e8aaa2a1aeca",
}

RUNTIME_HASHES = {
    "action_data_hash": "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1",
    "party_config_hash": "baff722d9ce79cf7f57891c439b7b3fd746ad76e779e4d582eaa51802eba2684",
    "transition_config_sha256": "210538d4bf99789d0af08ecff5fb76dc3f472f5b170a144d9f1b3b1f46116b9c",
    "buffs_sha256": "fe8b8fc63e8b9a3405a61ebe08a2cafa13f94dd4af91d1670b968df727cb554d",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_inventory_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = [
        {
            "path": str(entry["path"]).replace("\\", "/"),
            "bytes": int(entry["bytes"]),
            "sha256": str(entry["sha256"]).lower(),
        }
        for entry in entries
    ]
    normalized.sort(key=lambda entry: entry["path"])
    return normalized


def inventory_entry_digest(entries: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        normalized_inventory_entries(entries),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_reviewed_inventory(path: Path) -> dict[str, Any]:
    if sha256_file(path) != REVIEW_INVENTORY_FILE_SHA256:
        raise ValueError("Reviewed completed-result inventory file SHA-256 mismatch")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    entries = normalized_inventory_entries(payload.get("files", []))
    if int(payload.get("file_count", -1)) != EXPECTED_FILE_COUNT or len(entries) != EXPECTED_FILE_COUNT:
        raise ValueError("Reviewed completed-result inventory file count mismatch")
    if int(payload.get("total_bytes", -1)) != EXPECTED_TOTAL_BYTES:
        raise ValueError("Reviewed completed-result inventory byte count mismatch")
    if sum(entry["bytes"] for entry in entries) != EXPECTED_TOTAL_BYTES:
        raise ValueError("Reviewed completed-result inventory entry bytes mismatch")
    if len({entry["path"] for entry in entries}) != len(entries):
        raise ValueError("Reviewed completed-result inventory contains duplicate paths")
    if inventory_entry_digest(entries) != REVIEW_INVENTORY_ENTRY_DIGEST:
        raise ValueError("Reviewed completed-result normalized entry digest mismatch")
    for entry in entries:
        path_value = Path(entry["path"])
        if path_value.is_absolute() or ".." in path_value.parts:
            raise ValueError(f"Unsafe inventory path: {entry['path']}")
    return dict(payload) | {
        "files": entries,
        "inventory_file_sha256": REVIEW_INVENTORY_FILE_SHA256,
        "normalized_entry_digest_sha256": REVIEW_INVENTORY_ENTRY_DIGEST,
    }


def validate_inventory(output_root: Path, inventory: dict[str, Any]) -> dict[str, Any]:
    entries = inventory["files"]
    expected = {entry["path"]: entry for entry in entries}
    actual_paths = sorted(
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file()
    )
    missing = sorted(set(expected) - set(actual_paths))
    added = sorted(set(actual_paths) - set(expected))
    if missing or added:
        raise ValueError(f"Completed-result inventory path mismatch: missing={missing[:5]} added={added[:5]}")
    total_bytes = 0
    for relative in actual_paths:
        path = output_root / relative
        entry = expected[relative]
        size = path.stat().st_size
        if size != entry["bytes"]:
            raise ValueError(f"Completed-result inventory size mismatch: {relative}")
        digest = sha256_file(path)
        if digest != entry["sha256"]:
            raise ValueError(f"Completed-result inventory SHA-256 mismatch: {relative}")
        total_bytes += size
    if len(actual_paths) != EXPECTED_FILE_COUNT or total_bytes != EXPECTED_TOTAL_BYTES:
        raise ValueError("Completed-result aggregate inventory mismatch")
    return {
        "file_count": len(actual_paths),
        "total_bytes": total_bytes,
        "normalized_entry_digest_sha256": inventory_entry_digest(entries),
    }


def validate_review_archive(path: Path) -> dict[str, Any]:
    if sha256_file(path) != REVIEW_ARCHIVE_SHA256:
        raise ValueError("Completed-result review ZIP SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        if len(archive.infolist()) != 14 or archive.testzip() is not None:
            raise ValueError("Completed-result review ZIP structure or CRC mismatch")
    return {"path": path.as_posix(), "sha256": REVIEW_ARCHIVE_SHA256, "entry_count": 14}


def corrected_completed_metrics() -> dict[str, Any]:
    metrics = performance_accounting(
        cumulative_expansions=4908270,
        invocation_start_expansions=3000000,
        invocation_elapsed_seconds=7659.986105200136,
        prior_cumulative_elapsed_seconds=8955.554317099974,
        cumulative_accounting_complete=True,
    )
    metrics.update(
        {
            "schema_version": "beam_search_corrected_execution_metrics_v116",
            "source_execution_result_sha256": CORE_HASHES["execution_result.json"],
            "source_recorded_expansions_per_second": 640.7674808532514,
            "source_recorded_rate_status": "invalid_cumulative_expansions_divided_by_resume_invocation_elapsed",
            "first_invocation_expansions": 3000000,
            "first_invocation_elapsed_seconds": 8955.554317099974,
            "first_invocation_expansions_per_second": 334.9876393772433,
            "cumulative_wall_time_display": "approximately 4 hours 36 minutes 55.54 seconds",
        }
    )
    return metrics


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_completed_structure(project_root: Path, output_root: Path, *, replay: bool = True) -> dict[str, Any]:
    for relative, expected in CORE_HASHES.items():
        if sha256_file(output_root / relative) != expected:
            raise ValueError(f"Completed-result core SHA-256 mismatch: {relative}")
    if sha256_file(project_root / PLAN_PATH) != PLAN_SHA256:
        raise ValueError("Completed-result plan SHA-256 mismatch")
    state = _load_json(output_root / "search_state.json")
    result = _load_json(output_root / "execution_result.json")
    leaderboard = _load_json(output_root / "leaderboard.json")
    best_route = _load_json(output_root / "best_route.json")
    final_summary = _load_json(output_root / "final_summary.json")
    source_summary = _load_json(output_root / f"routes/{WINNER_ROUTE_ID}_summary.json")
    for payload in (state, result, final_summary):
        status = payload.get("termination_status", payload.get("status"))
        if status != "completed_search":
            raise ValueError("Completed result is not completed_search")
    if int(state["expansions"]) != 4908270 or int(result["expansions"]) != 4908270:
        raise ValueError("Completed result expansion count mismatch")
    if int(result["maximum_expansions"]) != 6500000:
        raise ValueError("Completed result safety maximum mismatch")
    completed_buckets = list(state.get("completed_buckets", []))
    if completed_buckets != list(range(240)):
        raise ValueError("Completed bucket set is not exactly 0..239")
    if state.get("pending_buckets") or result.get("pending_bucket_indices"):
        raise ValueError("Completed result still has pending buckets")
    if state.get("destination_bucket_accumulators") != {} or result.get("destination_bucket_accumulators") != {}:
        raise ValueError("Completed result still has destination accumulators")
    routes = list(result.get("completed_routes", []))
    if len(routes) != 128 or int(result.get("completed_route_count", -1)) != 128:
        raise ValueError("Completed retained route count mismatch")
    selected_hashes = [route["selected_sequence_sha256"] for route in routes]
    resolved_hashes = [route["resolved_sequence_sha256"] for route in routes]
    if len(set(selected_hashes)) != 128 or len(set(resolved_hashes)) != 128:
        raise ValueError("Completed route hashes are not unique")
    if any(float(route["combat_time"]) != 120.0 for route in routes):
        raise ValueError("A retained completed route is not 120 seconds")
    listed = leaderboard.get("completed_search_routes", [])
    if len(listed) != 128:
        raise ValueError("Leaderboard retained route count mismatch")
    listed_damage = [float(route["total_damage"]) for route in listed]
    if listed_damage != sorted(listed_damage, reverse=True):
        raise ValueError("Completed route leaderboard is not damage-sorted")
    winner = leaderboard["winner"]
    winner_route = winner["route"]
    expected_winner = {
        "route_id": WINNER_ROUTE_ID,
        "terminal_node_id": 4894495,
        "completion_order": 33081,
        "total_damage": WINNER_DAMAGE,
        "dps": WINNER_DPS,
        "combat_time": 120.0,
        "current_time": 195.73333333333346,
        "action_count": 162,
        "selected_sequence_sha256": WINNER_SELECTED_SHA256,
        "resolved_sequence_sha256": WINNER_RESOLVED_SHA256,
    }
    for key, expected in expected_winner.items():
        if winner_route.get(key) != expected:
            raise ValueError(f"Winning route mismatch: {key}")
    if winner["winner_kind"] != "beam_search_route" or winner_route != best_route["winner"]["route"]:
        raise ValueError("Winning route selection mismatch")
    if float(winner_route["total_damage"]) != max(float(route["total_damage"]) for route in routes):
        raise ValueError("Winning route is not maximum damage")
    if final_summary.get("global_optimum_proven") is not False:
        raise ValueError("Completed result incorrectly claims global optimality")
    if result.get("partial_nodes_excluded_from_final_winner") is not True:
        raise ValueError("Partial nodes were not excluded from completed winner selection")
    actual_hashes = result.get("actual_data_hashes", {})
    if actual_hashes.get("action_data_hash") != RUNTIME_HASHES["action_data_hash"]:
        raise ValueError("Completed result action-data hash mismatch")
    if actual_hashes.get("party_config_hash") != RUNTIME_HASHES["party_config_hash"]:
        raise ValueError("Completed result party-config hash mismatch")
    if action_data_hash(root=project_root) != RUNTIME_HASHES["action_data_hash"]:
        raise ValueError("Current action-data hash changed")
    if party_config_hash(root=project_root) != RUNTIME_HASHES["party_config_hash"]:
        raise ValueError("Current party-config hash changed")
    if sha256_file(project_root / "data/transition_config.json") != RUNTIME_HASHES["transition_config_sha256"]:
        raise ValueError("Current transition-config hash changed")
    if sha256_file(project_root / "data/buffs.json") != RUNTIME_HASHES["buffs_sha256"]:
        raise ValueError("Current buffs hash changed")
    if source_summary["selected_action_count"] != 162 or source_summary["resolved_action_count"] != 162 or source_summary["executed_action_count"] != 162:
        raise ValueError("Winning route action accounting mismatch")
    if not all(item["available_before_execution"] and item["executed"] for item in source_summary["attempted_actions"]):
        raise ValueError("Winning route source summary contains an unavailable/failed action")
    timeline_path = output_root / f"routes/{WINNER_ROUTE_ID}_timeline.csv"
    with timeline_path.open("r", encoding="utf-8", newline="") as file:
        timeline = list(csv.DictReader(file))
    if len(timeline) != 162 or sum(float(row["damage"]) for row in timeline) != 5651892.274552993:
        raise ValueError("Winning route timeline parity mismatch")
    truncated = [row for row in timeline if row["truncated_by_combat_limit"].lower() == "true"]
    if len(truncated) != 1 or truncated[0]["resolved_action_id"] != "lynae_echo_hyvatia":
        raise ValueError("Winning route horizon truncation mismatch")
    replay_summary = source_summary
    if replay:
        with tempfile.TemporaryDirectory(prefix="beam-v116-replay-") as temporary:
            replay_summary = replay_selected_route_to_files(
                selected_sequence=list(winner_route["selected_sequence"]),
                output_root=Path(temporary),
                route_id=WINNER_ROUTE_ID,
                combat_duration=120.0,
                terminal_record=winner_route,
            )
        if replay_summary["executed_action_count"] != 162 or replay_summary["final_combat_time"] != 120.0:
            raise ValueError("Winning route replay did not complete exactly")
    return {
        "state": state,
        "execution_result": result,
        "leaderboard": leaderboard,
        "best_route": best_route,
        "final_summary": final_summary,
        "source_winning_summary": source_summary,
        "replay_summary": replay_summary,
        "winning_route": winner_route,
        "completed_routes": routes,
    }


def validate_completed_result(
    *, project_root: Path, output_root: Path, review_inventory: Path, replay: bool = True
) -> dict[str, Any]:
    project_root = project_root.resolve()
    output_root = output_root.resolve()
    inventory = load_reviewed_inventory(review_inventory.resolve())
    inventory_validation = validate_inventory(output_root, inventory)
    structure = validate_completed_structure(project_root, output_root, replay=replay)
    return {"inventory": inventory, "inventory_validation": inventory_validation, **structure}


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(payload)
    os.replace(temp, path)


def _compact_route(route: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in route.items() if key not in {"selected_sequence", "resolved_sequence"}}


def build_compact_artifacts(
    *, project_root: Path, output_root: Path, review_inventory: Path
) -> dict[str, Any]:
    project_root = project_root.resolve()
    output_root = output_root.resolve()
    before = validate_completed_result(
        project_root=project_root,
        output_root=output_root,
        review_inventory=review_inventory,
        replay=True,
    )
    completed_root = project_root / COMPLETED_DIR
    inventory_payload = {
        "schema_version": "beam_search_v114_completed_inventory_v116",
        "result_root": HEAVY_OUTPUT.as_posix(),
        "file_count": EXPECTED_FILE_COUNT,
        "total_bytes": EXPECTED_TOTAL_BYTES,
        "reviewed_inventory_file_sha256": REVIEW_INVENTORY_FILE_SHA256,
        "normalized_entry_digest_sha256": REVIEW_INVENTORY_ENTRY_DIGEST,
        "files": before["inventory"]["files"],
    }
    _atomic_json(project_root / COMPLETED_INVENTORY_PATH, inventory_payload)
    _atomic_json(completed_root / "full_result_inventory.json", inventory_payload)
    metrics = corrected_completed_metrics()
    _atomic_json(completed_root / "corrected_execution_metrics.json", metrics)
    source_summary = dict(before["source_winning_summary"])
    references = current_reference_comparisons(WINNER_DAMAGE, root=project_root)
    source_summary.update(
        {
            "schema_version": "beam_search_winning_route_summary_v116",
            "source_summary_sha256": CORE_HASHES[f"routes/{WINNER_ROUTE_ID}_summary.json"],
            "comparison_against_references": references,
            "comparison_reference_labels": {
                "manual_v114": "current reviewed manual v114",
                "current_reviewed_model_incumbent": "best trained model",
                "historical_verified_bc": "historical reference only",
            },
        }
    )
    manual_damage = float(references["manual_v114"]["total_damage"])
    source_summary["route_comparison"] = dict(source_summary["route_comparison"]) | {
        "manual_v114_damage_delta": WINNER_DAMAGE - manual_damage,
        "manual_v114_damage_ratio": WINNER_DAMAGE / manual_damage,
        "legacy_manual_bc_damage_fields_status": "superseded_by_current_manual_v114_reference",
    }
    _atomic_json(completed_root / "winning_route_summary.json", source_summary)
    _atomic_bytes(
        completed_root / "winning_route_timeline.csv",
        (output_root / f"routes/{WINNER_ROUTE_ID}_timeline.csv").read_bytes(),
    )
    compact_routes = [_compact_route(route) for route in before["completed_routes"]]
    compact_routes.sort(key=lambda route: (-float(route["total_damage"]), int(route["completion_order"])))
    completed_routes_payload = {
        "schema_version": "beam_search_completed_routes_compact_v116",
        "route_count": 128,
        "all_routes_completed_120s": True,
        "selected_route_hashes_unique": True,
        "resolved_route_hashes_unique": True,
        "routes": compact_routes,
    }
    _atomic_json(completed_root / "completed_routes_compact.json", completed_routes_payload)
    winner = dict(before["leaderboard"]["winner"])
    winner["route"] = _compact_route(winner["route"])
    leaderboard_payload = {
        "schema_version": "beam_search_completed_leaderboard_v116",
        "objective": "deterministic_completed_120s_total_damage_only",
        "winner_selection": "maximum_total_damage_then_declared_order",
        "completed_route_count": 128,
        "partial_nodes_excluded_from_final_winner": True,
        "winner": winner,
        "completed_routes": compact_routes,
        "global_optimum_proven": False,
    }
    _atomic_json(completed_root / "leaderboard.json", leaderboard_payload)
    _atomic_json(
        completed_root / "best_route.json",
        {
            "schema_version": "beam_search_completed_best_route_v116",
            "winner": winner,
            "partial_nodes_excluded_from_final_winner": True,
            "global_optimum_proven": False,
        },
    )
    improvement = {
        "damage_delta": WINNER_DAMAGE - MODEL_DAMAGE,
        "relative_improvement_percent": (WINNER_DAMAGE / MODEL_DAMAGE - 1.0) * 100.0,
        "dps_delta": WINNER_DPS - MODEL_DPS,
    }
    final_summary_payload = {
        "schema_version": "beam_search_completed_final_summary_v116",
        "status": "completed_search",
        "termination_status": "completed_search",
        "stage_id": "full_120s_lowmem_32gb_v114",
        "expansions": 4908270,
        "configured_maximum_expansions": 6500000,
        "completed_buckets": 240,
        "pending_buckets": [],
        "completed_route_count": 128,
        "winner": winner,
        "previous_reviewed_incumbent": {
            "winner_kind": "trained_model",
            "model_path": MODEL_PATH,
            "model_sha256": MODEL_SHA256,
            "total_damage": MODEL_DAMAGE,
            "dps": MODEL_DPS,
        },
        "improvement": improvement,
        "performance": metrics,
        "global_optimum_proven": False,
    }
    _atomic_json(completed_root / "final_summary.json", final_summary_payload)
    after_inventory = validate_inventory(output_root, before["inventory"])
    validate_completed_structure(project_root, output_root, replay=False)
    artifact_names = [
        "final_summary.json",
        "leaderboard.json",
        "best_route.json",
        "winning_route_summary.json",
        "winning_route_timeline.csv",
        "corrected_execution_metrics.json",
        "completed_routes_compact.json",
        "full_result_inventory.json",
    ]
    artifact_hashes = {
        name: sha256_file(completed_root / name) for name in artifact_names
    }
    manifest = {
        "schema_version": "beam_search_v114_completed_result_manifest_v116",
        "ingestion_candidate": 116,
        "runtime_contract": "v114",
        "status": "completed_search",
        "termination_status": "completed_search",
        "stage_id": "full_120s_lowmem_32gb_v114",
        "plan_path": PLAN_PATH.as_posix(),
        "plan_sha256": PLAN_SHA256,
        "source_core_hashes": CORE_HASHES,
        "full_inventory": {
            "file_count": EXPECTED_FILE_COUNT,
            "total_bytes": EXPECTED_TOTAL_BYTES,
            "reviewed_inventory_file_sha256": REVIEW_INVENTORY_FILE_SHA256,
            "normalized_entry_digest_sha256": REVIEW_INVENTORY_ENTRY_DIGEST,
            "before_validation": before["inventory_validation"],
            "after_validation": after_inventory,
        },
        "completed_search": {
            "expansions": 4908270,
            "configured_maximum_expansions": 6500000,
            "completed_bucket_count": 240,
            "completed_bucket_indices": [0, 239],
            "pending_buckets": [],
            "destination_bucket_accumulators": {},
            "completed_retained_route_count": 128,
            "partial_nodes_excluded_from_winner": True,
        },
        "winning_route": _compact_route(before["winning_route"]),
        "previous_reviewed_incumbent": final_summary_payload["previous_reviewed_incumbent"],
        "exact_improvement": improvement,
        "corrected_performance": metrics,
        "original_heavy_output_path": HEAVY_OUTPUT.as_posix(),
        "heavy_output_preserved_locally": True,
        "heavy_output_mutated_by_ingestion": False,
        "global_optimum_proven": False,
        "artifact_sha256": artifact_hashes,
        "external_inventory_artifact_path": COMPLETED_INVENTORY_PATH.as_posix(),
        "external_inventory_artifact_sha256": sha256_file(project_root / COMPLETED_INVENTORY_PATH),
        "cleanup": {
            "applied": False,
            "eligible_categories": {
                "frontier/accumulators/": {"file_count": 836, "bytes": 2529324201},
                "results/beam_search_v114_lowmem_32gb/frontier/": {"file_count": 207, "bytes": 3838673},
            },
            "source_candidate_archive_must_be_validated_before_apply": True,
        },
    }
    _atomic_json(completed_root / "result_manifest.json", manifest)
    report_path = project_root / "reports/beam_search_v114_completed_v116.md"
    report = f"""# Completed v114 Beam Search result (candidate 116 ingestion)

## Search validity

The reviewed search terminated naturally with `completed_search` at 4,908,270 expansions, before the 6,500,000 safety maximum. All 240 half-second buckets (0-239) are complete, no pending bucket or destination accumulator remains, and 128 unique completed 120-second routes were retained.

## Winning damage result

The overall project winner is Beam route `{WINNER_ROUTE_ID}` at {WINNER_DAMAGE} total damage and {WINNER_DPS} DPS. All 162 selected actions were available and executed during replay. The selected/resolved route hashes remain `{WINNER_SELECTED_SHA256}` and `{WINNER_RESOLVED_SHA256}`.

The best trained model remains `{MODEL_PATH}` at {MODEL_DAMAGE} damage and {MODEL_DPS} DPS. Beam improves by {improvement['damage_delta']} damage ({improvement['relative_improvement_percent']}%) and {improvement['dps_delta']} DPS.

## Non-global-optimum status

Winner selection is deterministic completed-120-second total damage only. Beam is the best reviewed project result, but pruning prevents this search from proving a global optimum.

## Corrected performance accounting

The resume invocation added 1,908,270 expansions in 7,659.986105200136 seconds, or 249.12186181441405 expansions/s. Cumulative elapsed time is 16,615.54042230011 seconds (approximately 4h 36m 55.54s), giving 295.40236882169023 cumulative expansions/s. The historical 640.7674808532514 value incorrectly divided cumulative expansions by resume-only elapsed time.

## Comparison references

The corrected winning-route summary labels the current manual v114 reference ({references['manual_v114']['total_damage']}), the current reviewed model incumbent ({references['current_reviewed_model_incumbent']['total_damage']}), and the historical verified BC reference ({references['historical_verified_bc']['total_damage']}) separately.

## Safe cleanup status

The full 1,051-file, 2,538,957,524-byte heavy result was validated before and after ingestion and was not modified. Cleanup was not applied. After candidate 116 passes external review, the dry-run cleanup tool may report 836 accumulator files ({2529324201:,} bytes) plus 207 redundant nested frontier files ({3838673:,} bytes) as eligible, subject to all manifest/archive/replay guards.
"""
    _atomic_bytes(report_path, report.encode("utf-8"))
    return {
        "status": "completed_result_ingested_v116",
        "completed_root": completed_root.as_posix(),
        "result_manifest_sha256": sha256_file(completed_root / "result_manifest.json"),
        "inventory_file_count": EXPECTED_FILE_COUNT,
        "inventory_total_bytes": EXPECTED_TOTAL_BYTES,
        "inventory_entry_digest_sha256": REVIEW_INVENTORY_ENTRY_DIGEST,
        "heavy_before_after_equal": before["inventory_validation"] == after_inventory,
        "winning_route_id": WINNER_ROUTE_ID,
        "winning_damage": WINNER_DAMAGE,
        "winning_dps": WINNER_DPS,
    }


def validate_compact_manifest(project_root: Path) -> dict[str, Any]:
    root = project_root / COMPLETED_DIR
    manifest = _load_json(root / "result_manifest.json")
    if manifest.get("schema_version") != "beam_search_v114_completed_result_manifest_v116":
        raise ValueError("Compact completed-result manifest schema mismatch")
    if manifest.get("termination_status") != "completed_search":
        raise ValueError("Compact completed-result manifest is not completed")
    if manifest.get("global_optimum_proven") is not False:
        raise ValueError("Compact completed-result manifest claims global optimality")
    if manifest.get("full_inventory", {}).get("normalized_entry_digest_sha256") != REVIEW_INVENTORY_ENTRY_DIGEST:
        raise ValueError("Compact completed-result inventory digest mismatch")
    for name, expected in manifest.get("artifact_sha256", {}).items():
        if sha256_file(root / name) != expected:
            raise ValueError(f"Compact completed-result artifact hash mismatch: {name}")
    external = project_root / manifest["external_inventory_artifact_path"]
    if sha256_file(external) != manifest["external_inventory_artifact_sha256"]:
        raise ValueError("External compact inventory artifact hash mismatch")
    return manifest
