from __future__ import annotations

import argparse
import copy
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from search.mcts_production_result import (
    COMPACT_RESULT,
    SEEDS,
    load_compact_inventories,
    sha256_file,
    validate_compact,
)


ELIGIBLE = (
    "checkpoint/tree_00049000.npz",
    "checkpoint/tree_00050000.npz",
    "checkpoint/mast_00049000.npz",
    "checkpoint/mast_00050000.npz",
    "checkpoint/snapshots.dat",
)
REQUIRED_CORE = (
    "execution_result.json", "final_summary.json", "leaderboard.json", "best_route.json",
    "completed_routes_compact.json", "checkpoint/latest_manifest.json",
    "checkpoint/previous_manifest.json", "checkpoint/progression.json",
)
EXPECTED_RECLAIMABLE = {118001: 10078176, 118002: 10066745, 118003: 9920461}


def validate_candidate_archive(project_root: Path, archive_path: Path) -> dict[str, Any]:
    if not archive_path.is_file():
        return {"built": False, "path": archive_path.as_posix(), "sha256": None, "valid": False}
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("candidate-119 archive CRC failure")
        names = set(archive.namelist())
        required = {
            f"{COMPACT_RESULT.as_posix()}/result_manifest.json",
            "scripts/mcts_v118_production_cleanup_smoke_test.py",
            "scripts/cleanup_mcts_v118_production_payloads_v119.py",
        }
        if not required <= names:
            raise ValueError("candidate-119 archive lacks cleanup/compact-result contract")
        archived_manifest = archive.read(f"{COMPACT_RESULT.as_posix()}/result_manifest.json")
        if archived_manifest != (project_root / COMPACT_RESULT / "result_manifest.json").read_bytes():
            raise ValueError("candidate-119 archive compact manifest differs from source")
        if any(name.startswith("results/mcts_v118_32gb/production_50k_seed_") for name in names):
            raise ValueError("candidate-119 archive contains excluded raw production output")
    return {
        "built": True, "path": archive_path.as_posix(), "sha256": sha256_file(archive_path), "valid": True,
    }


def _inventory_map(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {str(row["path"]).replace("\\", "/"): row for row in inventory["files"]}
    if len(result) != len(inventory["files"]):
        raise ValueError("cleanup inventory contains duplicate paths")
    return result


def validate_seed_cleanup_preconditions(raw_root: Path, seed: int, inventory: dict[str, Any]) -> dict[str, Any]:
    expected = _inventory_map(inventory)
    actual = {path.relative_to(raw_root).as_posix(): path for path in raw_root.rglob("*") if path.is_file()}
    extras = sorted(set(actual) - set(expected))
    if extras:
        raise ValueError(f"seed {seed} cleanup inventory contains unexpected files: {extras}")
    missing = sorted(set(expected) - set(actual))
    if any(relative not in ELIGIBLE for relative in missing):
        raise ValueError(f"seed {seed} cleanup inventory is missing a non-eligible file")
    for relative, path in actual.items():
        row = expected[relative]
        if path.stat().st_size != int(row["bytes"]) or sha256_file(path) != row["sha256"]:
            raise ValueError(f"seed {seed} cleanup inventory mismatch: {relative}")
    for relative in REQUIRED_CORE:
        if relative not in actual:
            raise ValueError(f"seed {seed} cleanup required core file is missing: {relative}")
    latest = json.loads((raw_root / "checkpoint/latest_manifest.json").read_text(encoding="utf-8"))
    previous = json.loads((raw_root / "checkpoint/previous_manifest.json").read_text(encoding="utf-8"))
    if latest.get("simulation_count") != 50000 or latest.get("node_count") != 50001:
        raise ValueError(f"seed {seed} cleanup latest checkpoint is incomplete")
    if previous.get("simulation_count") != 49000 or previous.get("node_count") != 49001:
        raise ValueError(f"seed {seed} cleanup previous checkpoint is incomplete")
    eligible = []
    already_absent = []
    for relative in ELIGIBLE:
        row = expected.get(relative)
        if row is None:
            raise ValueError(f"seed {seed} cleanup approved payload is absent from reviewed inventory")
        if relative in actual:
            eligible.append({"path": relative, "bytes": int(row["bytes"]), "sha256": row["sha256"]})
        else:
            already_absent.append(relative)
    reviewed_bytes = sum(int(expected[relative]["bytes"]) for relative in ELIGIBLE)
    if reviewed_bytes != EXPECTED_RECLAIMABLE[seed]:
        raise ValueError(f"seed {seed} cleanup reviewed reclaimable byte total mismatch")
    return {"eligible": eligible, "already_absent": already_absent, "reviewed_reclaimable_bytes": reviewed_bytes}


def build_cleanup_plan(project_root: Path, candidate_archive: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    validate_compact(project_root)
    inventories = load_compact_inventories(project_root)
    seeds: dict[str, Any] = {}
    all_eligible: list[dict[str, Any]] = []
    for seed, expected in SEEDS.items():
        raw_root = project_root / "results" / "mcts_v118_32gb" / expected["stage_id"]
        checked = validate_seed_cleanup_preconditions(raw_root, seed, inventories[seed])
        entries = [dict(row, seed=seed, raw_root=raw_root.as_posix()) for row in checked["eligible"]]
        all_eligible.extend(entries)
        seeds[str(seed)] = checked
    archive = validate_candidate_archive(project_root, candidate_archive.resolve())
    return {
        "schema_version": "mcts_v118_production_cleanup_plan_v119", "mode": "dry_run",
        "candidate_archive": archive, "seeds": seeds, "eligible_files": all_eligible,
        "reclaimable_file_count": len(all_eligible),
        "reclaimable_bytes": sum(row["bytes"] for row in all_eligible),
        "reviewed_reclaimable_bytes": sum(EXPECTED_RECLAIMABLE.values()),
        "cleanup_applied": False,
    }


def apply_cleanup_plan(plan: dict[str, Any], *, externally_verified: bool) -> dict[str, Any]:
    if not externally_verified:
        raise ValueError("candidate 119 must be externally verified before cleanup apply")
    if not plan.get("candidate_archive", {}).get("valid"):
        raise ValueError("a valid candidate-119 archive is required before cleanup apply")
    deleted = 0
    already_absent = 0
    for item in plan["eligible_files"]:
        raw_root = Path(item["raw_root"]).resolve()
        path = (raw_root / item["path"]).resolve()
        if raw_root not in path.parents or item["path"] not in ELIGIBLE:
            raise ValueError("cleanup plan selected a path outside the exact allowlist")
        if not path.exists():
            already_absent += 1
            continue
        if path.stat().st_size != int(item["bytes"]) or sha256_file(path) != item["sha256"]:
            raise ValueError("cleanup payload changed after validation")
        path.unlink()
        deleted += 1
    result = copy.deepcopy(plan)
    result.update(
        mode="apply", cleanup_applied=True, deleted_file_count=deleted,
        already_absent_file_count=already_absent,
    )
    return result


def _progress_allows_apply(project_root: Path) -> bool:
    progress = json.loads((project_root / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    status = progress.get("status") or {}
    return str(status.get("latest_externally_verified_baseline")) == "119" and status.get("current_candidate") != "119"


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely clean completed v118 production checkpoint binaries")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--candidate-archive", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    project = args.project_root.resolve()
    archive = args.candidate_archive if args.candidate_archive.is_absolute() else (project / args.candidate_archive).resolve()
    plan = build_cleanup_plan(project, archive)
    result = apply_cleanup_plan(plan, externally_verified=_progress_allows_apply(project)) if args.apply else plan
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
