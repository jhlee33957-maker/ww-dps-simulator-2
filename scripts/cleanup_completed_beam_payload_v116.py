from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


COMPACT_ROOT = Path("results/beam_search_v114_completed_v116")
CORE_KEEP = {
    "best_route.json",
    "execution_result.json",
    "final_summary.json",
    "leaderboard.json",
    "search_state.json",
}
ELIGIBLE_PREFIXES = (
    "frontier/accumulators/",
    "results/beam_search_v114_lowmem_32gb/frontier/",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_compact_manifest(project_root: Path) -> tuple[Path, dict[str, Any]]:
    path = project_root / COMPACT_ROOT / "result_manifest.json"
    if not path.is_file():
        raise ValueError("Compact completed-result manifest is missing")
    manifest = _load(path)
    if manifest.get("schema_version") != "beam_search_v114_completed_result_manifest_v116":
        raise ValueError("Compact completed-result manifest schema mismatch")
    completed = manifest.get("completed_search") or {}
    if manifest.get("termination_status") != "completed_search":
        raise ValueError("Cleanup requires termination_status=completed_search")
    if int(completed.get("completed_bucket_count", -1)) != 240:
        raise ValueError("Cleanup requires all 240 completed buckets")
    if completed.get("pending_buckets") != [] or completed.get("destination_bucket_accumulators") != {}:
        raise ValueError("Cleanup rejects pending buckets or destination accumulators")
    if int(completed.get("completed_retained_route_count", -1)) != 128:
        raise ValueError("Cleanup requires exactly 128 retained completed routes")
    if manifest.get("heavy_output_mutated_by_ingestion") is not False:
        raise ValueError("Compact manifest does not prove read-only ingestion")
    full = manifest.get("full_inventory") or {}
    if full.get("before_validation") != full.get("after_validation"):
        raise ValueError("Compact manifest does not prove before/after inventory equality")
    for relative, expected in (manifest.get("artifact_sha256") or {}).items():
        artifact = project_root / COMPACT_ROOT / relative
        if sha256_file(artifact) != expected:
            raise ValueError(f"Compact artifact hash mismatch: {relative}")
    return path, manifest


def _validate_heavy_state(output_root: Path) -> dict[str, Any]:
    state = _load(output_root / "search_state.json")
    if state.get("termination_status") != "completed_search":
        raise ValueError("Heavy result is not completed_search")
    if state.get("completed_buckets") != list(range(240)):
        raise ValueError("Heavy result completed buckets mismatch")
    if state.get("pending_buckets") != [] or state.get("destination_bucket_accumulators") != {}:
        raise ValueError("Heavy result still has pending search payload references")
    if len(state.get("completed_routes", [])) != 128:
        raise ValueError("Heavy result completed route count mismatch")
    serialized = json.dumps(state, sort_keys=True, separators=(",", ":"))
    for prefix in ELIGIBLE_PREFIXES:
        if prefix in serialized:
            raise ValueError(f"Final state still references cleanup payload: {prefix}")
    return state


def _inventory_path(project_root: Path, manifest: dict[str, Any]) -> Path:
    relative = manifest.get("external_inventory_artifact_path")
    if not isinstance(relative, str):
        raise ValueError("Compact manifest has no inventory artifact path")
    path = project_root / relative
    expected = manifest.get("external_inventory_artifact_sha256")
    if expected and sha256_file(path) != expected:
        raise ValueError("Completed inventory artifact SHA-256 mismatch")
    return path


def _validate_inventory(output_root: Path, inventory: dict[str, Any]) -> list[dict[str, Any]]:
    entries = list(inventory.get("files", []))
    expected_paths = {str(entry["path"]).replace("\\", "/") for entry in entries}
    actual_paths = {
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file()
    }
    if expected_paths != actual_paths:
        raise ValueError("Heavy output no longer matches the validated full inventory")
    for entry in entries:
        relative = str(entry["path"]).replace("\\", "/")
        path = output_root / relative
        if path.stat().st_size != int(entry["bytes"]) or sha256_file(path) != entry["sha256"]:
            raise ValueError(f"Heavy inventory mismatch: {relative}")
    return entries


def _validate_archive(project_root: Path, manifest_path: Path, candidate_archive: Path) -> dict[str, Any]:
    if not candidate_archive.is_file():
        return {"built": False, "path": candidate_archive.as_posix(), "sha256": None}
    with zipfile.ZipFile(candidate_archive) as archive:
        if archive.testzip() is not None:
            raise ValueError("Candidate archive CRC validation failed")
        name = (COMPACT_ROOT / "result_manifest.json").as_posix()
        if name not in archive.namelist():
            raise ValueError("Candidate archive omits compact completed-result manifest")
        if hashlib.sha256(archive.read(name)).hexdigest() != sha256_file(manifest_path):
            raise ValueError("Candidate archive compact manifest differs from local manifest")
    return {"built": True, "path": candidate_archive.as_posix(), "sha256": sha256_file(candidate_archive)}


def cleanup_plan(
    *, project_root: Path, output_root: Path, candidate_archive: Path | None = None
) -> dict[str, Any]:
    project_root = project_root.resolve()
    output_root = output_root.resolve()
    manifest_path, manifest = _validate_compact_manifest(project_root)
    _validate_heavy_state(output_root)
    inventory = _load(_inventory_path(project_root, manifest))
    entries = _validate_inventory(output_root, inventory)
    eligible = [
        dict(entry) | {"path": str(entry["path"]).replace("\\", "/")}
        for entry in entries
        if str(entry["path"]).replace("\\", "/").startswith(ELIGIBLE_PREFIXES)
    ]
    archive_path = candidate_archive or project_root.parent / "ww-dps-simulator-2-116.zip"
    archive = _validate_archive(project_root, manifest_path, archive_path.resolve())
    return {
        "schema_version": "beam_search_completed_cleanup_plan_v116",
        "mode": "dry_run",
        "output_root": output_root.as_posix(),
        "eligible_file_count": len(eligible),
        "reclaimable_bytes": sum(int(entry["bytes"]) for entry in eligible),
        "categories": {
            prefix: {
                "file_count": sum(entry["path"].startswith(prefix) for entry in eligible),
                "bytes": sum(int(entry["bytes"]) for entry in eligible if entry["path"].startswith(prefix)),
            }
            for prefix in ELIGIBLE_PREFIXES
        },
        "eligible_files": eligible,
        "required_core_files": sorted(CORE_KEEP),
        "candidate_archive": archive,
        "apply_eligible": bool(archive["built"]),
        "cleanup_applied": False,
    }


def apply_cleanup(
    *, project_root: Path, output_root: Path, candidate_archive: Path | None = None
) -> dict[str, Any]:
    project_root = project_root.resolve()
    output_root = output_root.resolve()
    receipt_path = project_root / COMPACT_ROOT / "cleanup_receipt.json"
    if receipt_path.is_file():
        receipt = _load(receipt_path)
        for relative, expected in receipt.get("preserved_core_hashes", {}).items():
            if sha256_file(output_root / relative) != expected:
                raise ValueError(f"Preserved core changed after cleanup: {relative}")
        return receipt | {"idempotent_repeat": True}
    plan = cleanup_plan(
        project_root=project_root,
        output_root=output_root,
        candidate_archive=candidate_archive,
    )
    if not plan["apply_eligible"]:
        raise ValueError("Cleanup apply requires a successfully built candidate-116 archive")
    deleted: list[dict[str, Any]] = []
    root_text = output_root.as_posix().rstrip("/") + "/"
    for entry in plan["eligible_files"]:
        path = (output_root / entry["path"]).resolve()
        if not path.as_posix().startswith(root_text):
            raise ValueError(f"Refusing out-of-root cleanup path: {path}")
        path.unlink()
        deleted.append(entry)
    approved_roots = [output_root / "frontier/accumulators", output_root / "results/beam_search_v114_lowmem_32gb/frontier"]
    for approved in approved_roots:
        if approved.exists():
            for directory in sorted((p for p in approved.rglob("*") if p.is_dir()), reverse=True):
                try:
                    directory.rmdir()
                except OSError:
                    pass
            try:
                approved.rmdir()
            except OSError:
                pass
    preserved = {relative: sha256_file(output_root / relative) for relative in sorted(CORE_KEEP)}
    receipt = {
        "schema_version": "beam_search_completed_cleanup_receipt_v116",
        "status": "completed",
        "deleted_file_count": len(deleted),
        "reclaimed_bytes": sum(int(entry["bytes"]) for entry in deleted),
        "deleted_files": deleted,
        "preserved_core_hashes": preserved,
        "candidate_archive_sha256": plan["candidate_archive"]["sha256"],
        "compact_manifest_sha256": sha256_file(project_root / COMPACT_ROOT / "result_manifest.json"),
    }
    _atomic_json(receipt_path, receipt)
    return receipt | {"idempotent_repeat": False}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Safely remove validated completed Beam spill payloads.")
    result.add_argument("--project-root", type=Path, default=Path("."))
    result.add_argument("--output-root", type=Path, required=True)
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    result.add_argument("--candidate-archive", type=Path)
    return result


def main() -> None:
    args = parser().parse_args()
    project_root = args.project_root.resolve()
    output_root = args.output_root if args.output_root.is_absolute() else project_root / args.output_root
    archive = args.candidate_archive
    if archive is not None and not archive.is_absolute():
        archive = project_root / archive
    if args.apply:
        result = apply_cleanup(project_root=project_root, output_root=output_root, candidate_archive=archive)
    else:
        result = cleanup_plan(project_root=project_root, output_root=output_root, candidate_archive=archive)
    printable = dict(result)
    printable.pop("eligible_files", None)
    print(json.dumps(printable, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
