from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "runtime_cleanup_v113_receipt"
ABANDONED_REL = "results/beam_search_v111_full_120s"
CALIBRATION_REL = "results/beam_search_v111"
RECEIPT_REL = "results/runtime_cleanup_v113_receipt.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contains_completed_120s_route(root: Path) -> bool:
    for name in ("execution_result.json", "final_summary.json", "best_route.json", "leaderboard.json"):
        path = root / name
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return True
        text = json.dumps(payload, sort_keys=True)
        if '"combat_duration": 120' in text and any(token in text for token in ('"completed_route_count": 1', '"completed_search_routes": [{', '"winner": {')):
            return True
    return False


def _verified_output_marker(value: Any) -> bool:
    if isinstance(value, dict):
        direct_text = " ".join(str(item).lower() for item in value.values() if not isinstance(item, (dict, list)))
        if ABANDONED_REL in direct_text and "externally_verified" in direct_text and "completed" in direct_text:
            return True
        return any(_verified_output_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_verified_output_marker(item) for item in value)
    return False


def cleanup_candidates(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    project_root = project_root.resolve()
    abandoned = (project_root / ABANDONED_REL).resolve()
    calibration = (project_root / CALIBRATION_REL).resolve()
    proof = {
        "abandoned_output_root": ABANDONED_REL,
        "calibration_output_root": CALIBRATION_REL,
        "roots_are_distinct": abandoned != calibration,
        "completed_120s_route_found": _contains_completed_120s_route(abandoned) if abandoned.exists() else False,
        "external_verification_marker_found": False,
    }
    progress_path = project_root / "PROJECT_PROGRESS_STATE.json"
    if progress_path.exists():
        proof["external_verification_marker_found"] = _verified_output_marker(json.loads(progress_path.read_text(encoding="utf-8")))
    candidates: list[tuple[Path, str]] = []
    for directory_name in ("__pycache__", ".pytest_cache"):
        for directory in project_root.rglob(directory_name):
            relative_parts = directory.relative_to(project_root).parts
            if directory.is_dir() and not any(part in {".git", ".venv"} for part in relative_parts):
                candidates.append((directory, "cache"))
    for archive in project_root.glob("*.zip"):
        candidates.append((archive, "project archive inside source tree"))
    for temp in project_root.glob("results/*smoke*"):
        candidates.append((temp, "temporary smoke output"))
    if abandoned.exists():
        if not proof["roots_are_distinct"] or proof["completed_120s_route_found"] or proof["external_verification_marker_found"]:
            raise ValueError("Abandoned 64GB output did not satisfy cleanup proof")
        candidates.append((abandoned, "abandoned unverified 64GB Beam output with no completed 120-second route"))
    files: dict[str, dict[str, Any]] = {}
    for target, reason in candidates:
        paths = [target] if target.is_file() else sorted(item for item in target.rglob("*") if item.is_file())
        for path in paths:
            relative = path.resolve().relative_to(project_root).as_posix()
            if relative == RECEIPT_REL:
                continue
            files[relative] = {"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path), "reason": reason}
    return [files[key] for key in sorted(files)], proof


def cleanup(project_root: Path, *, apply: bool) -> dict[str, Any]:
    project_root = project_root.resolve()
    files, proof = cleanup_candidates(project_root)
    receipt_path = project_root / RECEIPT_REL
    previous = None
    if apply and receipt_path.exists():
        previous = json.loads(receipt_path.read_text(encoding="utf-8"))
    prior_files = list(previous.get("removed_files", [])) if previous else []
    combined_files = prior_files + [entry for entry in files if entry["path"] not in {item["path"] for item in prior_files}]
    receipt = {
        "schema_version": SCHEMA,
        "mode": "apply" if apply else "dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "proof": proof,
        "this_run_removed_file_count": len(files),
        "this_run_removed_bytes": sum(entry["bytes"] for entry in files),
        "removed_file_count": len(combined_files),
        "removed_bytes": sum(entry["bytes"] for entry in combined_files),
        "removed_files": combined_files,
    }
    if previous:
        receipt["previous_apply_generated_at_utc"] = previous.get("generated_at_utc")
    if apply:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        targets: set[Path] = set()
        for entry in files:
            path = project_root / entry["path"]
            if path.exists():
                path.unlink()
            targets.add(path.parent)
        for directory in sorted(targets, key=lambda item: len(item.parts), reverse=True):
            current = directory
            while current != project_root and current.exists():
                try:
                    current.rmdir()
                except OSError:
                    break
                current = current.parent
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely clean proven-disposable candidate runtime artifacts.")
    parser.add_argument("--project-root", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(cleanup(args.project_root, apply=bool(args.apply)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
