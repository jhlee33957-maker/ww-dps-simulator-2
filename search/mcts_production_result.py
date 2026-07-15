from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import statistics
import zipfile
from pathlib import Path
from typing import Any

from search.mcts_reporting import replay_completed_route
from search.mcts_result_role import resolve_mcts_result_role, result_role_fields


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = Path("data/mcts_plan_v118_32gb_3x50k.json")
PLAN_SHA256 = "2f5cb64f0a5b71a3957dadfbeff8f2c9ac7923b76e52ab410bcb805dc2f38562"
COMPACT_RESULT = Path("results/mcts_v118_production_3x50k_v119")
REPORT_PATH = Path("reports/mcts_v118_3x50k_production_v119.md")
BEAM = {
    "kind": "beam",
    "method": "completed Beam route",
    "route_id": "67a4250b3b8d0de9",
    "total_damage": 5651892.274552992,
    "dps": 47099.1022879416,
    "combat_time": 120.0,
    "completed": True,
}
MODEL = {
    "kind": "best_trained_model",
    "method": "guarded PPO 90k",
    "model_path": "models/guarded_ppo_v109/bc_conservative_seed_11/step_000090000.zip",
    "total_damage": 5276844.358692044,
    "dps": 43973.70298910037,
    "combat_time": 120.0,
    "completed": True,
}
MANUAL = {
    "kind": "manual_v114", "total_damage": 5268418.084869607,
    "dps": 43903.484040580064, "combat_time": 120.0, "completed": True,
}
HISTORICAL_BC = {
    "kind": "historical_bc", "total_damage": 5165134.682363356,
    "dps": 43042.78901969464, "combat_time": 120.0, "completed": True,
}
CALIBRATION = {
    "kind": "mcts_20k_calibration", "seed": 117001, "route_id": "5aab329ce5b526a7",
    "total_damage": 4128137.812582737, "dps": 34401.14843818948,
    "combat_time": 120.0, "completed": True, "result_role": "calibration",
}


SEEDS: dict[int, dict[str, Any]] = {
    118001: {
        "stage_id": "production_50k_seed_118001", "file_count": 22, "total_bytes": 18311501,
        "inventory_digest": "f9cc98539e19c590cce4faed1ab2da904034da7a930f24c54e7e646ef430caed",
        "review_archive_sha256": "3ca5fdcd4042e412bc49f31d4d1d302bc4b580bab7cc5724849c9359f48932c9",
        "review_zip_entries": 21, "route_id": "4d32f291ea1bbe80",
        "damage": 3957306.530795142, "dps": 32977.55442329285, "current_time": 172.21666666666675,
        "actions": 193, "completion_simulation": 30820, "plateau": 19180,
        "selected_sha": "4d32f291ea1bbe801600cd74eea4931e880b58a082c8cffffef220ebade97b46",
        "resolved_sha": "1d87f5ad2be74b935cefcf29c6354ab4bfe4bcdf21c397f6bbbe25727945295f",
        "elapsed": 8619.5546521, "action_executions": 9258172, "peak_rss": 98148352,
        "core_hashes": {
            "execution_result.json": "347d00464c87b652de37915203feb464681ad245f7535b7889471947f12d95f8",
            "final_summary.json": "156cc1352b7298e7cd8ff6a8b89de81f2d07732508cd244f7def99f7c4f6ad77",
            "leaderboard.json": "d71c52cfec2d652775b3767423cd077a31ab0ad8aecd32f4a52a6b5711b34087",
            "completed_routes_compact.json": "d71c52cfec2d652775b3767423cd077a31ab0ad8aecd32f4a52a6b5711b34087",
            "best_route.json": "b0ac0fbff548240bc8e2e1444963f9fe1ceae091f7f4746b43339fb8043af1b3",
            "routes/4d32f291ea1bbe80_summary.json": "0e97c42d8d7294f9bb6633bed19449b3b938d51b72f22a558b22b8d3377f294c",
            "routes/4d32f291ea1bbe80_timeline.csv": "379a01367e84e7aaf254e08fd89413a8cd70be5e26a3177656c787f0b73f3a5c",
            "checkpoint/latest_manifest.json": "44cdc05bedc84f087c85f5eada77075baaef4954b57964623f71ee3a455e5c81",
            "checkpoint/previous_manifest.json": "816d179302a26bc94a0918b61b1cc36605591e3bf3cc0950495659a639a408c4",
            "checkpoint/progression.json": "02a077489b92a316364e4575d9cec20fe360113e5304fd116be031e5b9240484",
        },
    },
    118002: {
        "stage_id": "production_50k_seed_118002", "file_count": 22, "total_bytes": 18133192,
        "inventory_digest": "9c8fa27171101295735e74022238a63bcb905c2218f6efde1d9a344044bce6c9",
        "review_archive_sha256": "bead09a4097d3ce479bca6d7772653b4f7a41042659bb3f2e0f0bd1abc30455a",
        "review_zip_entries": 20, "route_id": "33330b882697c345",
        "damage": 4456165.094682989, "dps": 37134.70912235824, "current_time": 170.8666666666666,
        "actions": 174, "completion_simulation": 38749, "plateau": 11251,
        "selected_sha": "33330b882697c3459a2be511d9b1765e20a503295d50bd40e2cfeaecb198c937",
        "resolved_sha": "900c87948a4a3828f137d11ae0d841f6c92e40ba38bfde386f777cac4f50d148",
        "elapsed": 7343.211269500001, "action_executions": 8672985, "peak_rss": 118767616,
        "core_hashes": {
            "execution_result.json": "ed39b143bbeacf2a7c5862ca13cce59ae2b99401486b102732b70f49537de558",
            "final_summary.json": "23c6a80d4f7fda13315739b18877ee30c59607f07566983ba63f0e9ae70a5617",
            "leaderboard.json": "775abae76bcbbe6ad1b437d6516a9a376a59730b2781b47385f50e2fc25031a2",
            "completed_routes_compact.json": "775abae76bcbbe6ad1b437d6516a9a376a59730b2781b47385f50e2fc25031a2",
            "best_route.json": "82c7f2bad63eb653d886127f4779192cfcdc73a30fed28731fb5aca5c15cb90c",
            "routes/33330b882697c345_summary.json": "dba12e8f41a25229231b8a0dedcb6a08561523fe4921b0ac4dd113af923ee3c8",
            "routes/33330b882697c345_timeline.csv": "c81aa23f945b7a294444d322330cdcd08ee376ca44fd4cf65c5c4a2f582abc36",
            "checkpoint/latest_manifest.json": "b28820d175b818b38c54979fc0ab0f49ab08589ebe997d3af19ae4fa59ad20b1",
            "checkpoint/previous_manifest.json": "cb5ffa4b5a950cfeb008f07805d60b65098388cd450ea5e2113d58753158548c",
            "checkpoint/progression.json": "112d1e28ec05c92b8893f44ee9be1489dc37fb1e2e78997c35fdc649004677b6",
        },
    },
    118003: {
        "stage_id": "production_50k_seed_118003", "file_count": 22, "total_bytes": 18035546,
        "inventory_digest": "5c2508efc7c0bf51205a6b0d200d2ffc04e9566cb5575ea7f9df9b4c53086046",
        "review_archive_sha256": "3e7016fd5371e3dc32cc4c262e3d2003af0deb66930956e74401661d6e109dd8",
        "review_zip_entries": 20, "route_id": "d3dcc3f4b372ac5d",
        "damage": 4647724.703247974, "dps": 38731.039193733115, "current_time": 169.54999999999993,
        "actions": 174, "completion_simulation": 11285, "plateau": 38715,
        "selected_sha": "d3dcc3f4b372ac5d897c0b8ebf81260b3b1dae97363e21814d914c0bc70878e4",
        "resolved_sha": "f44a05ea9c7d4e9345b04ff79e258a704ce3d7ea15fe9a3cbe26598953845f0b",
        "elapsed": 6440.801855199999, "action_executions": 8721594, "peak_rss": 118153216,
        "logical_result_sha": "79d1f9c554fb7748471d7ff11e3e2dd553c542f43626f14008f22639db125f0c",
        "rng_sha": "78c8f9ad43aa8596e5b7c34542cf9ace6d13f5b33a3da7f90788c3fae4814ed1",
        "mast_sha": "cf891a284d0d47a9f5a8250bb568f9d73b8bfd433e9031bc0146c742c3c1fb50",
        "core_hashes": {
            "execution_result.json": "d59b44126aa3125cf129a22ccf457c68b19a15d7bd6317d24ca1cdc078d3041e",
            "final_summary.json": "be08027781680b98c061abdc757fdec35707c70ee54096a7863139adf13e5134",
            "leaderboard.json": "32ffa3c320d92664bc05c382dda807b943b27d9959ab9d3c569ef44df2bc319e",
            "completed_routes_compact.json": "32ffa3c320d92664bc05c382dda807b943b27d9959ab9d3c569ef44df2bc319e",
            "best_route.json": "71f2f1aef6830ce0c5c514d017d60cb144d5ff8219df506cde3fbcbff1af4a42",
            "routes/d3dcc3f4b372ac5d_summary.json": "d2008053866773e6ab5f50eb8ef9622431bdbae81fe130a5b10860e7b599a766",
            "routes/d3dcc3f4b372ac5d_timeline.csv": "f49575097a6155bc4ec23d16131923ef97bb87792cc7c00e9efc364c90873d71",
            "checkpoint/latest_manifest.json": "d53219766138a3a43f7396504ad3dc775b750e8df510db1213b6dcdba72e6026",
            "checkpoint/previous_manifest.json": "8f323f71aa6fa37cf569d812892117f6b59869d4b6f863dce0b61cdd45758e4d",
            "checkpoint/progression.json": "92685de3013bf98cd461dc2ec8dbe294ee4d39e1f816caedb01d512088173f84",
        },
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_inventory_digest(entries: list[dict[str, Any]]) -> str:
    rows = sorted(
        (str(row["path"]).replace("\\", "/"), int(row["bytes"]), str(row["sha256"]).lower())
        for row in entries
    )
    payload = "".join(f"{path}\t{size}\t{digest}\n" for path, size, digest in rows).encode()
    return hashlib.sha256(payload).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _review_inventory(project_root: Path, seed: int) -> dict[str, Any]:
    expected = SEEDS[seed]
    archive_path = project_root / f"mcts_v118_seed_{seed}_50k_review.zip"
    if not archive_path.is_file() or sha256_file(archive_path) != expected["review_archive_sha256"]:
        raise ValueError(f"seed {seed} review archive SHA-256 mismatch")
    with zipfile.ZipFile(archive_path) as archive:
        if len(archive.infolist()) != expected["review_zip_entries"] or archive.testzip() is not None:
            raise ValueError(f"seed {seed} review archive entry/CRC mismatch")
    inventory_path = project_root / f"mcts_v118_seed_{seed}_50k_review" / "FULL_RESULT_FILE_INVENTORY.json"
    inventory = _load(inventory_path)
    if inventory.get("stage_id") != expected["stage_id"]:
        raise ValueError(f"seed {seed} reviewed inventory stage mismatch")
    _validate_inventory_metadata(seed, inventory)
    return inventory


def _validate_inventory_metadata(seed: int, inventory: dict[str, Any]) -> None:
    expected = SEEDS[seed]
    entries = inventory.get("files")
    if not isinstance(entries, list) or len(entries) != expected["file_count"]:
        raise ValueError(f"seed {seed} inventory file count mismatch")
    if inventory.get("file_count") != expected["file_count"]:
        raise ValueError(f"seed {seed} inventory declared file count mismatch")
    if inventory.get("total_bytes") != expected["total_bytes"] or sum(int(row["bytes"]) for row in entries) != expected["total_bytes"]:
        raise ValueError(f"seed {seed} inventory total bytes mismatch")
    if normalized_inventory_digest(entries) != expected["inventory_digest"]:
        raise ValueError(f"seed {seed} normalized inventory digest mismatch")
    paths = [str(row["path"]).replace("\\", "/") for row in entries]
    if len(paths) != len(set(paths)) or any(Path(path).is_absolute() or ".." in Path(path).parts for path in paths):
        raise ValueError(f"seed {seed} inventory path safety/uniqueness mismatch")


def _validate_inventory_files(seed: int, root: Path, inventory: dict[str, Any]) -> dict[str, Any]:
    _validate_inventory_metadata(seed, inventory)
    expected = {str(row["path"]).replace("\\", "/"): row for row in inventory["files"]}
    actual = {path.relative_to(root).as_posix(): path for path in root.rglob("*") if path.is_file()}
    if set(actual) != set(expected):
        raise ValueError(
            f"seed {seed} exact inventory paths mismatch: missing={sorted(set(expected)-set(actual))} "
            f"added={sorted(set(actual)-set(expected))}"
        )
    for relative, path in actual.items():
        row = expected[relative]
        if path.stat().st_size != int(row["bytes"]) or sha256_file(path) != row["sha256"]:
            raise ValueError(f"seed {seed} raw inventory mismatch: {relative}")
    return {
        "file_count": len(actual), "total_bytes": sum(path.stat().st_size for path in actual.values()),
        "normalized_inventory_digest_sha256": normalized_inventory_digest(inventory["files"]),
    }


def _snapshot_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256_file(path) for path in sorted(root.rglob("*")) if path.is_file()}


def validate_seed(
    project_root: Path,
    seed: int,
    raw_root: Path,
    inventory: dict[str, Any],
    *,
    replay: bool = True,
) -> dict[str, Any]:
    expected = SEEDS[seed]
    inventory_validation = _validate_inventory_files(seed, raw_root, inventory)
    for relative, digest in expected["core_hashes"].items():
        if sha256_file(raw_root / relative) != digest:
            raise ValueError(f"seed {seed} reviewed core hash mismatch: {relative}")
    execution = _load(raw_root / "execution_result.json")
    leaderboard = _load(raw_root / "leaderboard.json")
    final = _load(raw_root / "final_summary.json")
    exact_execution = {
        "stage_id": expected["stage_id"], "seed": seed,
        "termination_status": "simulation_budget_exhausted", "simulations_requested": 50000,
        "simulations_completed": 50000, "completed_rollout_count": 50000,
        "invalid_rollout_count": 0, "node_count": 50001, "normal_process_exit": True,
        "global_optimum_proven": False,
    }
    for key, value in exact_execution.items():
        if execution.get(key) != value:
            raise ValueError(f"seed {seed} execution {key} mismatch")
    if final.get("calibration_only") is not True:
        raise ValueError(f"seed {seed} raw reporting defect is not the reviewed calibration_only=true value")
    routes = leaderboard.get("routes")
    if not isinstance(routes, list) or len(routes) != 128 or leaderboard.get("retained_route_count") != 128:
        raise ValueError(f"seed {seed} retained route count mismatch")
    if any(float(route.get("combat_time", -1)) != 120.0 for route in routes):
        raise ValueError(f"seed {seed} includes a non-completed retained route")
    selected = [route.get("selected_sequence_sha256") for route in routes]
    resolved = [route.get("resolved_sequence_sha256") for route in routes]
    if len(set(selected)) != 128 or len(set(resolved)) != 128:
        raise ValueError(f"seed {seed} retained route hashes are not unique")
    order = [(float(route["total_damage"]), route["selected_sequence_sha256"]) for route in routes]
    if order != sorted(order, key=lambda item: (-item[0], item[1])):
        raise ValueError(f"seed {seed} leaderboard ordering mismatch")
    winner = leaderboard.get("winner")
    winner_exact = {
        "route_id": expected["route_id"], "total_damage": expected["damage"], "dps": expected["dps"],
        "combat_time": 120.0, "current_time": expected["current_time"], "action_count": expected["actions"],
        "completion_simulation_index": expected["completion_simulation"],
        "selected_sequence_sha256": expected["selected_sha"], "resolved_sequence_sha256": expected["resolved_sha"],
    }
    for key, value in winner_exact.items():
        if winner.get(key) != value:
            raise ValueError(f"seed {seed} winner {key} mismatch")
    if winner != routes[0]:
        raise ValueError(f"seed {seed} winner is not the top retained route")
    latest = _load(raw_root / "checkpoint/latest_manifest.json")
    previous = _load(raw_root / "checkpoint/previous_manifest.json")
    for manifest, simulation, nodes in ((latest, 50000, 50001), (previous, 49000, 49001)):
        if manifest.get("simulation_count") != simulation or manifest.get("node_count") != nodes:
            raise ValueError(f"seed {seed} checkpoint count mismatch")
        if manifest.get("plan_sha256") != PLAN_SHA256:
            raise ValueError(f"seed {seed} checkpoint plan SHA mismatch")
        for file_entry in (manifest.get("files") or {}).values():
            payload = raw_root / "checkpoint" / file_entry["path"]
            if payload.stat().st_size != int(file_entry["bytes"]) or sha256_file(payload) != file_entry["sha256"]:
                raise ValueError(f"seed {seed} checkpoint reference mismatch: {file_entry['path']}")
    replay_summary = None
    if replay:
        replay_summary = replay_completed_route(winner)
        replay_exact = {
            "selected_action_count": expected["actions"], "resolved_action_count": expected["actions"],
            "executed_action_count": expected["actions"], "selected_sequence_sha256": expected["selected_sha"],
            "resolved_sequence_sha256": expected["resolved_sha"], "total_damage": expected["damage"],
            "final_combat_time": 120.0,
        }
        for key, value in replay_exact.items():
            if replay_summary.get(key) != value:
                raise ValueError(f"seed {seed} replay {key} mismatch")
    return {
        "seed": seed, "raw_root": raw_root, "inventory": inventory,
        "inventory_validation": inventory_validation, "execution": execution,
        "leaderboard": leaderboard, "winner": winner, "latest": latest, "previous": previous,
        "source_summary": _load(raw_root / f"routes/{expected['route_id']}_summary.json"),
        "replay_summary": replay_summary,
        "progression": _load(raw_root / "checkpoint/progression.json"),
    }


def _seed_roots(project_root: Path, supplied: dict[int, Path] | None) -> dict[int, Path]:
    if supplied is not None:
        return {seed: path.resolve() for seed, path in supplied.items()}
    return {
        seed: project_root / "results" / "mcts_v118_32gb" / expected["stage_id"]
        for seed, expected in SEEDS.items()
    }


def validate_all(
    project_root: Path,
    *,
    seed_roots: dict[int, Path] | None = None,
    inventories: dict[int, dict[str, Any]] | None = None,
    replay: bool = True,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    if sha256_file(project_root / PLAN_PATH) != PLAN_SHA256:
        raise ValueError("reviewed v118 production plan SHA-256 mismatch")
    plan = _load(project_root / PLAN_PATH)
    roots = _seed_roots(project_root, seed_roots)
    if inventories is None:
        inventories = {seed: _review_inventory(project_root, seed) for seed in SEEDS}
    stage_by_id = {stage["stage_id"]: stage for stage in plan["stages"]}
    validated: dict[int, dict[str, Any]] = {}
    selected_all: set[str] = set()
    resolved_all: set[str] = set()
    for seed, expected in SEEDS.items():
        role = resolve_mcts_result_role(
            PLAN_PATH, PLAN_SHA256, expected["stage_id"], stage_by_id[expected["stage_id"]], root=project_root
        )
        if role != "production":
            raise ValueError(f"seed {seed} did not resolve as production")
        item = validate_seed(project_root, seed, roots[seed], inventories[seed], replay=replay)
        selected = {route["selected_sequence_sha256"] for route in item["leaderboard"]["routes"]}
        resolved = {route["resolved_sequence_sha256"] for route in item["leaderboard"]["routes"]}
        if selected_all & selected or resolved_all & resolved:
            raise ValueError("retained route hashes are not unique across production seeds")
        selected_all |= selected; resolved_all |= resolved
        validated[seed] = item
    return {"plan": plan, "seed_roots": roots, "seeds": validated}


def project_comparison() -> dict[str, Any]:
    mcts = [
        {
            "kind": f"mcts_seed_{seed}", "seed": seed, "route_id": item["route_id"],
            "total_damage": item["damage"], "dps": item["dps"], "combat_time": 120.0,
            "completed": True, "result_role": "production",
        }
        for seed, item in SEEDS.items()
    ]
    candidates = [BEAM, MODEL, MANUAL, HISTORICAL_BC, *mcts, CALIBRATION]
    winner = max(candidates, key=lambda row: float(row["total_damage"]))
    return {
        "schema_version": "current_project_comparison_v119",
        "selection": "maximum_deterministic_completed_120s_total_damage_only",
        "labels_do_not_affect_numerical_winner": True,
        "partial_routes_compete": False,
        "candidates": candidates,
        "overall_project_winner": winner,
        "best_trained_model": MODEL,
        "best_mcts_production_result": mcts[-1],
        "global_optimum_proven": False,
    }


def aggregate_summary() -> dict[str, Any]:
    damages = [SEEDS[seed]["damage"] for seed in SEEDS]
    elapsed = 22403.5677768
    actions = sum(SEEDS[seed]["action_executions"] for seed in SEEDS)
    best = SEEDS[118003]
    beam_delta = best["damage"] - BEAM["total_damage"]
    model_delta = best["damage"] - MODEL["total_damage"]
    return {
        "schema_version": "mcts_v118_3x50k_aggregate_summary_v119",
        "result_role": "production", "calibration_only": False, "production_search_result": True,
        "simulations": 150000, "completed_rollouts": 150000, "invalid_rollouts": 0, "nodes_created": 150003,
        "elapsed_seconds": elapsed, "total_action_executions": actions,
        "combined_action_executions_per_second": actions / elapsed,
        "highest_observed_rss_bytes": max(SEEDS[seed]["peak_rss"] for seed in SEEDS),
        "distribution": {
            "mean": statistics.mean(damages), "median": statistics.median(damages),
            "population_standard_deviation": statistics.pstdev(damages), "range": max(damages) - min(damages),
        },
        "winner": {
            "seed": 118003, "route_id": best["route_id"], "total_damage": best["damage"], "dps": best["dps"],
            "selected_sequence_sha256": best["selected_sha"], "resolved_sequence_sha256": best["resolved_sha"],
        },
        "comparison": {
            "delta_vs_beam_damage": beam_delta,
            "relative_delta_vs_beam_percent": -17.76692694278993,
            "delta_vs_best_trained_model_damage": model_delta,
            "relative_delta_vs_best_trained_model_percent": -11.92227044574058,
        },
        "extension_recommended": False,
        "stopping_evidence": "three long post-best plateaus and a 17.77% remaining gap to Beam",
        "global_optimum_proven": False,
    }


def _write_report(project_root: Path, aggregate: dict[str, Any]) -> None:
    comparison = aggregate["comparison"]
    text = f"""# MCTS v118 3x50k production result (candidate 119)

Candidate 119 ingests the three independently completed production seeds. It is pending external review.

## Ranking

1. seed 118003 — `d3dcc3f4b372ac5d`, 4,647,724.703247974 damage (38,731.039193733115 DPS)
2. seed 118002 — `33330b882697c345`, 4,456,165.094682989 damage (37,134.70912235824 DPS)
3. seed 118001 — `4d32f291ea1bbe80`, 3,957,306.530795142 damage (32,977.55442329285 DPS)

All winners replayed through the normal diagnostic simulator with exact selected/resolved hashes, exact damage, and 120.0 seconds of combat time. All 384 retained routes were completed 120-second routes.

## Aggregate

- 150,000 simulations and completed rollouts; 0 invalid rollouts; 150,003 nodes
- Mean damage: {aggregate['distribution']['mean']}
- Median damage: {aggregate['distribution']['median']}
- Population standard deviation: {aggregate['distribution']['population_standard_deviation']}
- Range: {aggregate['distribution']['range']}
- Runtime: {aggregate['elapsed_seconds']} seconds
- Total action executions: {aggregate['total_action_executions']}
- Combined throughput: {aggregate['combined_action_executions_per_second']} actions/s
- Highest observed RSS: {aggregate['highest_observed_rss_bytes']} bytes

## Plateaus and comparison

- seed 118001: best at simulation 30,820; 19,180 simulations without improvement
- seed 118002: best at simulation 38,749; 11,251 simulations without improvement
- seed 118003: best at simulation 11,285; 38,715 simulations without improvement
- Best MCTS versus Beam: {comparison['delta_vs_beam_damage']} damage ({comparison['relative_delta_vs_beam_percent']}%)
- Best MCTS versus guarded PPO 90k: {comparison['delta_vs_best_trained_model_damage']} damage ({comparison['relative_delta_vs_best_trained_model_percent']}%)

The completed Beam route remains the overall project winner and guarded PPO 90k remains the best trained model. No 100k/200k MCTS extension is recommended: every seed had a long post-best plateau and the best seed still trails Beam by more than one million damage. This is stopping evidence, not proof that more MCTS could never improve. No global optimum is claimed.
"""
    path = project_root / REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_compact_artifacts(
    project_root: Path,
    *,
    seed_roots: dict[int, Path],
) -> dict[str, Any]:
    project_root = project_root.resolve()
    raw_before = {seed: _snapshot_hashes(path) for seed, path in seed_roots.items()}
    inventories = {seed: _review_inventory(project_root, seed) for seed in SEEDS}
    validated = validate_all(project_root, seed_roots=seed_roots, inventories=inventories, replay=True)
    compact = project_root / COMPACT_RESULT
    compact.mkdir(parents=True, exist_ok=True)
    plan = validated["plan"]
    stage_by_id = {stage["stage_id"]: stage for stage in plan["stages"]}

    inventory_payload = {
        "schema_version": "mcts_v118_3x50k_full_result_inventories_v119",
        "plan_sha256": PLAN_SHA256,
        "seeds": {},
    }
    ranking: list[dict[str, Any]] = []
    progression: dict[str, Any] = {
        "schema_version": "mcts_v118_3x50k_production_progression_v119",
        "plateau_interpretation": "stopping_evidence_not_global_optimum_proof",
        "global_optimum_proven": False,
        "seeds": {},
    }
    for seed, item in validated["seeds"].items():
        expected = SEEDS[seed]
        role = resolve_mcts_result_role(
            PLAN_PATH, PLAN_SHA256, expected["stage_id"], stage_by_id[expected["stage_id"]], root=project_root
        )
        flags = result_role_fields(role)
        seed_dir = compact / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        final = {
            "schema_version": "mcts_production_seed_final_summary_v119",
            "stage_id": expected["stage_id"], "seed": seed,
            "termination_status": "simulation_budget_exhausted", "simulations_completed": 50000,
            "completed_rollouts": 50000, "invalid_rollouts": 0, "node_count": 50001,
            "winner": item["winner"], "elapsed_seconds": expected["elapsed"],
            "total_action_executions": expected["action_executions"], "peak_rss_bytes": expected["peak_rss"],
            **flags,
        }
        _atomic_json(seed_dir / "final_summary.json", final)
        shutil.copyfile(seed_roots[seed] / "best_route.json", seed_dir / "best_route.json")
        shutil.copyfile(
            seed_roots[seed] / f"routes/{expected['route_id']}_summary.json",
            seed_dir / "winning_route_summary.json",
        )
        shutil.copyfile(
            seed_roots[seed] / f"routes/{expected['route_id']}_timeline.csv",
            seed_dir / "winning_route_timeline.csv",
        )
        inventory_payload["seeds"][str(seed)] = {
            "stage_id": expected["stage_id"], "result_root": inventory_payload_root(project_root, seed_roots[seed]),
            "file_count": expected["file_count"], "total_bytes": expected["total_bytes"],
            "normalized_inventory_digest_sha256": expected["inventory_digest"],
            "core_hashes_before": expected["core_hashes"], "files": inventories[seed]["files"],
        }
        ranking.append({
            "rank": 0, "seed": seed, "route_id": expected["route_id"], "total_damage": expected["damage"],
            "dps": expected["dps"], "completion_simulation": expected["completion_simulation"],
            "plateau_length": expected["plateau"], "selected_sequence_sha256": expected["selected_sha"],
            "resolved_sequence_sha256": expected["resolved_sha"], "result_role": "production",
        })
        progression["seeds"][str(seed)] = {
            "best_first_found_simulation": expected["completion_simulation"],
            "simulations_without_improvement_after_best": expected["plateau"],
            "checkpoints": item["progression"]["checkpoints"],
            "global_optimum_proven": False,
        }
    ranking.sort(key=lambda row: -float(row["total_damage"]))
    for index, row in enumerate(ranking, 1):
        row["rank"] = index
    _atomic_json(compact / "seed_leaderboard.json", {
        "schema_version": "mcts_v118_3x50k_seed_leaderboard_v119", "ranking": ranking,
        "winner": ranking[0], "global_optimum_proven": False,
    })
    aggregate = aggregate_summary()
    _atomic_json(compact / "aggregate_summary.json", aggregate)
    _atomic_json(compact / "comparison.json", project_comparison())
    _atomic_json(compact / "production_progression.json", progression)
    _atomic_json(compact / "full_result_inventories.json", inventory_payload)
    _write_report(project_root, aggregate)

    raw_after = {seed: _snapshot_hashes(path) for seed, path in seed_roots.items()}
    if raw_before != raw_after:
        raise RuntimeError("raw reviewed production outputs changed during candidate-119 ingestion")
    for seed in SEEDS:
        inventory_payload["seeds"][str(seed)]["core_hashes_after"] = {
            relative: raw_after[seed][relative] for relative in SEEDS[seed]["core_hashes"]
        }
        inventory_payload["seeds"][str(seed)]["raw_files_unchanged"] = True
    _atomic_json(compact / "full_result_inventories.json", inventory_payload)

    artifact_hashes = {
        path.relative_to(compact).as_posix(): sha256_file(path)
        for path in sorted(compact.rglob("*")) if path.is_file() and path.name != "result_manifest.json"
    }
    manifest = {
        "schema_version": "mcts_v118_3x50k_result_manifest_v119",
        "candidate": 119, "external_review_status": "pending", "external_verification_claimed": False,
        "plan_path": PLAN_PATH.as_posix(), "plan_sha256": PLAN_SHA256,
        "result_role_contract_path": "data/mcts_result_role_compatibility_v119.json",
        "result_role_contract_sha256": sha256_file(project_root / "data/mcts_result_role_compatibility_v119.json"),
        "source_raw_outputs_preserved": True, "source_raw_outputs_mutated": False,
        "aggregate": aggregate, "artifact_sha256": artifact_hashes,
        "global_optimum_proven": False,
    }
    _atomic_json(compact / "result_manifest.json", manifest)
    return {"status": "ingested", "manifest": manifest, "manifest_sha256": sha256_file(compact / "result_manifest.json")}


def inventory_payload_root(project_root: Path, raw_root: Path) -> str:
    try:
        return raw_root.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return raw_root.resolve().as_posix()


def load_compact_inventories(project_root: Path) -> dict[int, dict[str, Any]]:
    payload = _load(project_root / COMPACT_RESULT / "full_result_inventories.json")
    if payload.get("schema_version") != "mcts_v118_3x50k_full_result_inventories_v119":
        raise ValueError("compact production inventory schema mismatch")
    result: dict[int, dict[str, Any]] = {}
    for seed in SEEDS:
        item = payload.get("seeds", {}).get(str(seed))
        if not isinstance(item, dict):
            raise ValueError(f"compact production inventory missing seed {seed}")
        inventory = {
            "stage_id": item["stage_id"], "file_count": item["file_count"],
            "total_bytes": item["total_bytes"], "files": item["files"],
        }
        _validate_inventory_metadata(seed, inventory)
        result[seed] = inventory
    return result


def validate_compact(project_root: Path) -> dict[str, Any]:
    compact = project_root / COMPACT_RESULT
    manifest = _load(compact / "result_manifest.json")
    if manifest.get("schema_version") != "mcts_v118_3x50k_result_manifest_v119":
        raise ValueError("compact production manifest schema mismatch")
    if manifest.get("candidate") != 119 or manifest.get("external_review_status") != "pending":
        raise ValueError("compact production candidate/review status mismatch")
    if manifest.get("plan_sha256") != PLAN_SHA256 or manifest.get("global_optimum_proven") is not False:
        raise ValueError("compact production plan/global-optimum contract mismatch")
    for relative, digest in manifest.get("artifact_sha256", {}).items():
        if sha256_file(compact / relative) != digest:
            raise ValueError(f"compact production artifact hash mismatch: {relative}")
    aggregate = _load(compact / "aggregate_summary.json")
    if aggregate != aggregate_summary():
        raise ValueError("compact production aggregate summary mismatch")
    comparison = _load(compact / "comparison.json")
    if comparison != project_comparison():
        raise ValueError("compact current-project comparison mismatch")
    inventories = load_compact_inventories(project_root)
    for seed in SEEDS:
        final = _load(compact / f"seed_{seed}/final_summary.json")
        if final.get("result_role") != "production" or final.get("calibration_only") is not False:
            raise ValueError(f"compact seed {seed} production role mismatch")
        if final.get("production_search_result") is not True or final.get("global_optimum_proven") is not False:
            raise ValueError(f"compact seed {seed} production flags mismatch")
    return {"manifest": manifest, "aggregate": aggregate, "comparison": comparison, "inventories": inventories}
