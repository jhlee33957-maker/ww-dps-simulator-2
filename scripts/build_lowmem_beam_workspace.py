from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "lowmem_beam_workspace_manifest_v113"
RECEIPT_SCHEMA = "lowmem_beam_workspace_build_receipt_v113"
VERIFIED_ARCHIVE = "ww-dps-simulator-2-112.zip"
VERIFIED_ARCHIVE_SHA256 = "b602af3cd1b87cac1529baa23042e023ce2c90e9d1560426567943da95515fc5"
PLAN_REL = "data/beam_search_plan_v113_32gb.json"
REQUIRED_FILES = (
    PLAN_REL,
    "data/beam_search_plan_v111.json",
    "data/generated/manual_120s_bc_demonstration_v105.npz",
    "data/manual_120s_baseline_routes_v104.json",
    "direct_action_data_patch_manifest_v61.json",
    "data/source/direct_action_data_patch_manifest_v61.json",
    "search/run_beam_search.py",
    "search/beam_search.py",
    "search/beam_spill.py",
    "search/beam_plan.py",
    "search/beam_reporting.py",
    "search/beam_state.py",
    "scripts/build_lowmem_beam_result_archive.py",
    "scripts/beam_search_lowmem_spill_streaming_smoke_test.py",
    "scripts/beam_search_lowmem_spill_finalization_count_smoke_test.py",
    "scripts/beam_search_lowmem_spill_no_repeated_rescan_smoke_test.py",
    "scripts/beam_search_lowmem_probe_phase_timing_smoke_test.py",
    "scripts/beam_search_lowmem_10000_probe_smoke_test.py",
    "scripts/beam_search_lowmem_10000_probe_repeatability_smoke_test.py",
    "PROJECT_PROGRESS_STATE.json",
    "progress_dashboard.py",
)
IMMUTABLE_HASHES = {
    "action_data_hash": "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1",
    "party_config_hash": "bd106ba1c0f5581436c35fea736a00fd6ad92b131f8b43ba8cf1e3dc89cbcb11",
    "direct_action_manifest_sha256": "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d",
    "bc_npz_sha256": "b020a1b9309b46bd87eb3fff4837aead53035c4c84620962f47feb9fc11846ff",
    "bc_model_sha256": "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e",
    "prior_ppo_model_sha256": "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513",
    "manual_route_raw_sha256": "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exclusion_reason(relative: str) -> str | None:
    parts = relative.split("/")
    name = parts[-1]
    lower = relative.lower()
    if any(part in {".git", ".venv", "__pycache__", ".pytest_cache"} for part in parts):
        return "development metadata, environment, or cache"
    if name.endswith((".pyc", ".pyo")):
        return "generated Python cache"
    if name.endswith(".zip"):
        return "project/archive or historical model bytes not needed by Beam runtime"
    if lower.startswith("models/"):
        return "historical training/model artifact; immutable hash retained in manifest"
    if lower.startswith("results/beam_search_v111_full_120s/"):
        return "abandoned unverified 64GB Beam output"
    if "smoke" in lower and (lower.startswith("results/") or lower.startswith("tmp/")):
        return "temporary smoke output"
    if lower.startswith("results/") and (
        "/frontier/" in lower or "/accumulators/" in lower or lower.endswith(".log") or lower.endswith("timeline.csv")
    ):
        return "historical runtime frontier, accumulator, timeline, or log"
    if name.endswith((".tmp", ".temp")):
        return "temporary artifact"
    return None


def inventory(source: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for path in sorted((item for item in source.rglob("*") if item.is_file()), key=lambda item: item.relative_to(source).as_posix()):
        relative = path.relative_to(source).as_posix()
        entry = {"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        reason = exclusion_reason(relative)
        if reason:
            excluded.append(entry | {"reason": reason})
        else:
            included.append(entry)
    return included, excluded


def build_manifest(source: Path, included: list[dict[str, Any]], excluded: list[dict[str, Any]]) -> dict[str, Any]:
    included_paths = {entry["path"] for entry in included}
    missing = sorted(set(REQUIRED_FILES) - included_paths)
    if missing:
        raise ValueError(f"Required low-memory files are missing or excluded: {missing}")
    plan_path = source / PLAN_REL
    return {
        "schema_version": SCHEMA,
        "source_project_path": ".",
        "source_verified_archive": {
            "name": VERIFIED_ARCHIVE,
            "sha256": VERIFIED_ARCHIVE_SHA256,
        },
        "included_file_count": len(included),
        "included_bytes": sum(entry["bytes"] for entry in included),
        "excluded_file_count": len(excluded),
        "excluded_bytes": sum(entry["bytes"] for entry in excluded),
        "included_files": included,
        "excluded_files": excluded,
        "files_required_for_low_memory_execution": list(REQUIRED_FILES),
        "low_memory_beam_plan": {"path": PLAN_REL, "sha256": sha256_file(plan_path)},
        "verified_immutable_artifact_hashes": IMMUTABLE_HASHES,
        "audit_preservation_statement": "full audit artifacts remain preserved in the externally verified candidate-112 archive",
        "global_optimum_claimed": False,
    }


def validate_paths(source: Path, output: Path, *, overwrite_empty: bool) -> None:
    source = source.resolve()
    output = output.resolve()
    if output == source or source in output.parents:
        raise ValueError("Output must not equal or be inside the source project root")
    if output.exists():
        if any(output.iterdir()):
            raise ValueError("Output directory must be empty")
        if not overwrite_empty:
            raise ValueError("Existing empty output requires --overwrite-empty")


def build_workspace(source: Path, output: Path, *, apply: bool, overwrite_empty: bool = False) -> dict[str, Any]:
    source = source.resolve()
    output = output.resolve()
    validate_paths(source, output, overwrite_empty=overwrite_empty)
    included, excluded = inventory(source)
    manifest = build_manifest(source, included, excluded)
    if not apply:
        return {"status": "dry_run", "output": output.as_posix(), "manifest": manifest}
    output.mkdir(parents=True, exist_ok=True)
    for entry in included:
        destination = output / entry["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / entry["path"], destination)
    manifest_path = output / "LOWMEM_WORKSPACE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_path": "LOWMEM_WORKSPACE_MANIFEST.json",
        "manifest_sha256": sha256_file(manifest_path),
    }
    (output / "LOWMEM_WORKSPACE_BUILD_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    for entry in included:
        copied = output / entry["path"]
        if sha256_file(copied) != entry["sha256"]:
            raise ValueError(f"Copied file hash mismatch: {entry['path']}")
    return {"status": "applied", "output": output.as_posix(), "manifest": manifest, "receipt": receipt}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a non-destructive slim Beam runtime workspace.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--apply", action="store_true")
    parser.add_argument("--overwrite-empty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_workspace(args.source, args.output, apply=bool(args.apply), overwrite_empty=args.overwrite_empty)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
