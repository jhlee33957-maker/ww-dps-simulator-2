from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
import copy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from search.mcts_completed_result import CORE_HASHES, load_compact_review_inventory
from search.mcts_reporting import replay_completed_route

COMPACT = Path("results/mcts_v117_calibration_20k_v118")
GENERATION = re.compile(r"^(tree|mast|rng|completed|snapshot_index)_(\d{8})\.(npz|json)$")
RETAINED_GENERATIONS = (19000, 20000)
REQUIRED_CORE_FILES = tuple(CORE_HASHES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()


def validate_compact(project_root: Path) -> dict[str, Any]:
    compact = project_root / COMPACT
    inventory = load_compact_review_inventory(project_root)
    manifest = inventory["result_manifest"]
    for relative, expected in manifest["artifact_sha256"].items():
        if sha256(compact / relative) != expected: raise ValueError(f"compact artifact hash mismatch: {relative}")
    winner = json.loads((compact / "best_route.json").read_text(encoding="utf-8"))["winner"]
    replay = replay_completed_route(winner)
    if replay["resolved_sequence_sha256"] != winner["resolved_sequence_sha256"] or replay["total_damage"] != winner["total_damage"]:
        raise ValueError("compact winner replay mismatch")
    if not manifest["calibration_only"] or manifest["production_mcts_executed"] or manifest["global_optimum_proven"]:
        raise ValueError("compact calibration status mismatch")
    return {"manifest": manifest, "inventory": inventory, "winner_replay": replay}


def validate_archive(project_root: Path, candidate_archive: Path) -> dict[str, Any]:
    if not candidate_archive.is_file(): return {"built": False, "path": candidate_archive.as_posix(), "sha256": None}
    relative = f"{COMPACT.as_posix()}/result_manifest.json"
    with zipfile.ZipFile(candidate_archive) as archive:
        if archive.testzip() is not None: raise ValueError("candidate archive CRC failure")
        names = set(archive.namelist())
        required = {relative, "scripts/manual_120s_bc_final_archive_integrity_smoke_test.py",
                    "scripts/mcts_v117_calibration_cleanup_smoke_test.py",
                    "scripts/mcts_v118_compact_inventory_self_contained_smoke_test.py"}
        if not required <= names:
            raise ValueError("candidate archive lacks exact-checker/compact-result contract")
        if archive.read(relative) != (project_root / relative).read_bytes():
            raise ValueError("candidate archive compact manifest differs from validated source")
        if "mcts_v117_20k_review.zip" in names or any(
            name.startswith("results/mcts_v117_32gb/calibration_20k_seed_117001/") for name in names
        ):
            raise ValueError("candidate archive contains excluded raw/review calibration evidence")
    return {"built": True, "path": candidate_archive.as_posix(), "sha256": sha256(candidate_archive)}


def _inventory_by_path(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = inventory.get("files")
    if not isinstance(entries, list): raise ValueError("cleanup inventory has no file list")
    result = {str(item["path"]).replace("\\", "/"): item for item in entries}
    if len(result) != len(entries): raise ValueError("cleanup inventory contains duplicate paths")
    return result


def validate_cleanup_inventory(*, output_root: Path, inventory: dict[str, Any],
                               retained_generations: tuple[int, int]) -> dict[str, Any]:
    expected = _inventory_by_path(inventory)
    actual = {path.relative_to(output_root).as_posix(): path for path in output_root.rglob("*") if path.is_file()}
    extras = sorted(set(actual) - set(expected))
    if extras: raise ValueError(f"cleanup raw inventory contains unexpected files: {extras[:5]}")
    missing = sorted(set(expected) - set(actual))
    for relative in missing:
        match = GENERATION.match(Path(relative).name)
        if match is None or int(match.group(2)) in retained_generations:
            raise ValueError(f"cleanup raw inventory is missing a required file: {relative}")
    for relative, path in actual.items():
        entry = expected[relative]
        if path.stat().st_size != int(entry["bytes"]) or sha256(path) != entry["sha256"]:
            raise ValueError(f"cleanup raw inventory mismatch: {relative}")
    return {"file_count": int(inventory["file_count"]), "total_bytes": int(inventory["total_bytes"]),
            "normalized_entry_digest_sha256": inventory["normalized_entry_digest_sha256"],
            "validated_existing_file_count": len(actual), "already_removed_eligible_file_count": len(missing)}


def validate_cleanup_preconditions(*, output_root: Path, inventory: dict[str, Any],
                                   calibration_complete: bool, winning_route_replay_valid: bool,
                                   retained_generations: tuple[int, int] = RETAINED_GENERATIONS,
                                   required_core_files: tuple[str, ...] = REQUIRED_CORE_FILES) -> dict[str, Any]:
    if not calibration_complete: raise ValueError("cleanup requires a completed 20k calibration")
    if not winning_route_replay_valid: raise ValueError("cleanup requires a valid winning-route replay")
    latest_path = output_root / "checkpoint/latest_manifest.json"
    previous_path = output_root / "checkpoint/previous_manifest.json"
    try:
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
        previous = json.loads(previous_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("cleanup checkpoint manifests are incomplete") from error
    if int(latest.get("simulation_count", -1)) != retained_generations[1]:
        raise ValueError("cleanup latest checkpoint generation mismatch")
    if int(previous.get("simulation_count", -1)) != retained_generations[0]:
        raise ValueError("cleanup previous checkpoint generation mismatch")
    expected = _inventory_by_path(inventory)
    for relative in required_core_files:
        path = output_root / relative
        if relative not in expected or not path.is_file():
            raise ValueError(f"cleanup required core result is missing: {relative}")
    validation = validate_cleanup_inventory(output_root=output_root, inventory=inventory,
                                            retained_generations=retained_generations)
    return {"inventory_validation": validation, "latest_manifest": latest, "previous_manifest": previous}


def select_reclaimable_checkpoint_generations(*, output_root: Path,
                                              retained_generations: tuple[int, int]) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    checkpoint = output_root / "checkpoint"
    for path in sorted(checkpoint.iterdir()):
        match = GENERATION.match(path.name)
        if match and int(match.group(2)) not in retained_generations:
            eligible.append({"path": path.relative_to(output_root).as_posix(), "bytes": path.stat().st_size,
                             "sha256": sha256(path)})
    return eligible


def build_validated_cleanup_plan(*, output_root: Path, preconditions: dict[str, Any],
                                 candidate_archive: dict[str, Any], compact_manifest_sha256: str,
                                 retained_generations: tuple[int, int] = RETAINED_GENERATIONS) -> dict[str, Any]:
    eligible = select_reclaimable_checkpoint_generations(output_root=output_root,
                                                         retained_generations=retained_generations)
    return {"schema_version": "mcts_v117_calibration_cleanup_plan_v118", "mode": "dry_run",
            "output_root": output_root.resolve().as_posix(), "compact_manifest_sha256": compact_manifest_sha256,
            "full_inventory_validated": preconditions["inventory_validation"], "winning_route_replay_valid": True,
            "calibration_complete": True, "production_independence_valid": True,
            "retained_generations": list(retained_generations), "eligible_files": eligible,
            "reclaimable_file_count": len(eligible), "reclaimable_bytes": sum(item["bytes"] for item in eligible),
            "candidate_archive": candidate_archive, "cleanup_applied": False}


def apply_validated_cleanup_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if not plan["candidate_archive"]["built"]:
        raise ValueError("candidate-118 archive must exist and pass exact structural validation before cleanup")
    output_root = Path(plan["output_root"]).resolve(); retained = {int(value) for value in plan["retained_generations"]}
    deleted = 0; already_absent = 0
    for item in plan["eligible_files"]:
        path = (output_root / item["path"]).resolve()
        if output_root not in path.parents: raise ValueError("cleanup path escapes the raw output root")
        match = GENERATION.match(path.name)
        if match is None or int(match.group(2)) in retained:
            raise ValueError("cleanup plan attempts to delete a retained/non-generation file")
        if not path.exists(): already_absent += 1; continue
        if path.stat().st_size != int(item["bytes"]) or sha256(path) != item["sha256"]:
            raise ValueError("cleanup payload changed after validation")
        path.unlink(); deleted += 1
    result = copy.deepcopy(plan); result.update(mode="apply", cleanup_applied=True,
                                                deleted_file_count=deleted,
                                                already_absent_file_count=already_absent)
    return result


def cleanup_plan(*, project_root: Path, output_root: Path, candidate_archive: Path) -> dict[str, Any]:
    project_root = project_root.resolve(); output_root = output_root.resolve(); candidate_archive = candidate_archive.resolve()
    compact = validate_compact(project_root); manifest = compact["manifest"]
    plan = json.loads((project_root / "data/mcts_plan_v118_32gb_3x50k.json").read_text(encoding="utf-8"))
    if any(stage.get("initial_tree") != "empty" or stage.get("initial_mast") != "empty" or stage.get("import_prior_route")
           for stage in plan["stages"]): raise ValueError("production plan imports calibration search state")
    preconditions = validate_cleanup_preconditions(
        output_root=output_root, inventory=compact["inventory"],
        calibration_complete=manifest["calibration"]["simulations"] == 20000,
        winning_route_replay_valid=compact["winner_replay"]["resolved_sequence_sha256"] ==
        manifest["calibration"]["winner"]["resolved_sequence_sha256"],
    )
    return build_validated_cleanup_plan(
        output_root=output_root, preconditions=preconditions,
        candidate_archive=validate_archive(project_root, candidate_archive),
        compact_manifest_sha256=sha256(project_root / COMPACT / "result_manifest.json"),
    )


def apply_cleanup(*, project_root: Path, output_root: Path, candidate_archive: Path) -> dict[str, Any]:
    plan = cleanup_plan(project_root=project_root, output_root=output_root, candidate_archive=candidate_archive)
    return apply_validated_cleanup_plan(plan)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True); parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(); mode.add_argument("--dry-run", action="store_true"); mode.add_argument("--apply", action="store_true")
    args = parser.parse_args(); project = args.project_root.resolve(); output = args.output_root.resolve()
    archive = args.candidate_archive if args.candidate_archive.is_absolute() else (project / args.candidate_archive).resolve()
    result = apply_cleanup(project_root=project, output_root=output, candidate_archive=archive) if args.apply else cleanup_plan(
        project_root=project, output_root=output, candidate_archive=archive)
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
