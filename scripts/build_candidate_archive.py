from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.guarded_ppo import (  # noqa: E402
    DEFAULT_PLAN_PATH,
    load_plan,
    path_from_state,
    validate_checkpoint_sidecar,
)


DEFAULT_ARCHIVE = ROOT.parent / "ww-dps-simulator-2-120.zip"
STATE_PATH = ROOT / "results" / "guarded_ppo_v109" / "experiment_state.json"
EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", "bc_eval_bundle"}
IMMUTABLE_MODEL_ZIP_FILES = {
    "models/maskable_ppo_bc_v105.zip",
    "models/maskable_ppo_candidate_after_bc_v105.zip",
}
HEAVY_BEAM_OUTPUT = Path("results/beam_search_v114_lowmem_32gb")
LOCAL_ONLY_BEAM_INVENTORY = Path("results/beam_search_v114_3m_checkpoint_inventory_v115.json")
LOCAL_ONLY_REVIEW_PACKAGES = {
    Path("beam_search_v114_3m_review"),
    Path("beam_search_v115_6p5m_review"),
    Path("mcts_v117_20k_review"),
    Path("mcts_v118_seed_118001_50k_review"),
    Path("mcts_v118_seed_118002_50k_review"),
    Path("mcts_v118_seed_118003_50k_review"),
}
RAW_MCTS_CALIBRATION = Path("results/mcts_v117_32gb/calibration_20k_seed_117001")
RAW_MCTS_PRODUCTION = tuple(
    Path(f"results/mcts_v118_32gb/production_50k_seed_{seed}")
    for seed in (118001, 118002, 118003)
)
LOCAL_ONLY_REVIEW_FILES = {Path("make_mcts_v118_seed_118003_review.ps1")}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a cache-free rootless candidate archive.")
    parser.add_argument("--output", type=Path, default=DEFAULT_ARCHIVE)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    result = build_archive(args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def build_archive(output: Path) -> dict[str, Any]:
    output = output.resolve()
    root = ROOT.resolve()
    required_zip_files = _required_zip_files_from_completed_state()
    if output == root:
        raise ValueError(f"Archive output must be a ZIP file path, not the project root: {output}")
    if output.exists():
        if output.is_dir():
            raise ValueError(f"Archive output path is a directory, not a ZIP file: {output}")
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)
    excluded_cache_count = 0
    excluded_zip_count = 0
    excluded_venv_or_git_count = 0
    entry_count = 0
    excluded_heavy_checkpoint_count = 0
    excluded_heavy_checkpoint_bytes = 0
    excluded_local_inventory_bytes = 0
    excluded_local_review_package_count = 0
    excluded_local_review_package_bytes = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(ROOT.rglob("*")):
            rel = path.relative_to(ROOT)
            parts = set(rel.parts)
            if path.is_dir():
                continue
            if path.resolve() == output:
                excluded_zip_count += 1
                continue
            if rel == HEAVY_BEAM_OUTPUT or HEAVY_BEAM_OUTPUT in rel.parents:
                excluded_heavy_checkpoint_count += 1
                excluded_heavy_checkpoint_bytes += path.stat().st_size
                continue
            if rel == RAW_MCTS_CALIBRATION or RAW_MCTS_CALIBRATION in rel.parents:
                excluded_heavy_checkpoint_count += 1
                excluded_heavy_checkpoint_bytes += path.stat().st_size
                continue
            if any(rel == raw or raw in rel.parents for raw in RAW_MCTS_PRODUCTION):
                excluded_heavy_checkpoint_count += 1
                excluded_heavy_checkpoint_bytes += path.stat().st_size
                continue
            if rel == LOCAL_ONLY_BEAM_INVENTORY:
                excluded_local_inventory_bytes = path.stat().st_size
                continue
            if any(rel == package or package in rel.parents for package in LOCAL_ONLY_REVIEW_PACKAGES):
                excluded_local_review_package_count += 1
                excluded_local_review_package_bytes += path.stat().st_size
                continue
            if rel in LOCAL_ONLY_REVIEW_FILES:
                excluded_local_review_package_count += 1
                excluded_local_review_package_bytes += path.stat().st_size
                continue
            if "__pycache__" in parts or ".pytest_cache" in parts or path.suffix in {".pyc", ".pyo"}:
                excluded_cache_count += 1
                continue
            if parts & {".git", ".venv", ".mypy_cache", "bc_eval_bundle"}:
                excluded_venv_or_git_count += 1
                continue
            if path.suffix == ".zip" and rel.as_posix() not in required_zip_files:
                excluded_zip_count += 1
                continue
            zf.write(path, rel.as_posix())
            entry_count += 1
    return {
        "archive_path": output.as_posix(),
        "archive_sha256": _sha256(output),
        "entry_count": entry_count,
        "included_model_zip_count": len(required_zip_files),
        "excluded_cache_count": excluded_cache_count,
        "excluded_zip_count": excluded_zip_count,
        "excluded_venv_git_or_bundle_count": excluded_venv_or_git_count,
        "excluded_heavy_checkpoint_path": HEAVY_BEAM_OUTPUT.as_posix(),
        "excluded_heavy_checkpoint_count": excluded_heavy_checkpoint_count,
        "excluded_heavy_checkpoint_bytes": excluded_heavy_checkpoint_bytes,
        "excluded_local_inventory_path": LOCAL_ONLY_BEAM_INVENTORY.as_posix(),
        "excluded_local_inventory_bytes": excluded_local_inventory_bytes,
        "excluded_local_review_package_paths": sorted(path.as_posix() for path in LOCAL_ONLY_REVIEW_PACKAGES),
        "excluded_local_review_package_count": excluded_local_review_package_count,
        "excluded_local_review_package_bytes": excluded_local_review_package_bytes,
    }


def _required_zip_files_from_completed_state() -> set[str]:
    if not STATE_PATH.exists():
        raise ValueError(f"Completed guarded PPO state is required for candidate 114 archive: {STATE_PATH}")
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    plan = load_plan(DEFAULT_PLAN_PATH)
    branches_by_id = {branch["branch_id"]: branch for branch in plan["branches"]}
    required = set(IMMUTABLE_MODEL_ZIP_FILES)
    referenced_guarded: set[str] = set()
    checkpoint_count = 0
    for branch_id, branch_state in state.get("branches", {}).items():
        branch = branches_by_id.get(branch_id)
        if branch is None:
            raise ValueError(f"State contains unknown guarded branch: {branch_id}")
        parent_model_path: Path | None = _initial_parent_model_path(branch)
        for record in sorted(branch_state.get("chunks", []), key=lambda item: int(item.get("chunk_index", -1))):
            if record.get("kind") != "guarded_ppo_checkpoint":
                continue
            checkpoint_count += 1
            checkpoint = path_from_state(record["checkpoint_path"])
            rel = checkpoint.relative_to(ROOT).as_posix()
            referenced_guarded.add(rel)
            required.add(rel)
            expected_hash = record.get("checkpoint_sha256")
            if not checkpoint.exists():
                raise ValueError(f"State-referenced guarded checkpoint is missing: {rel}")
            if expected_hash != _sha256(checkpoint):
                raise ValueError(f"State-referenced guarded checkpoint hash mismatch: {rel}")
            metadata = path_from_state(record["metadata_path"])
            if record.get("metadata_sha256") != _sha256(metadata):
                raise ValueError(f"State-referenced guarded checkpoint sidecar hash mismatch: {metadata}")
            validate_checkpoint_sidecar(
                branch=branch,
                chunk_index=int(record["chunk_index"]),
                plan_path=DEFAULT_PLAN_PATH,
                model_path=checkpoint,
                metadata_path=metadata,
                parent_model_path=parent_model_path,
            )
            parent_model_path = checkpoint
    if checkpoint_count != 30:
        raise ValueError(f"Expected exactly 30 completed guarded checkpoints, found {checkpoint_count}")
    orphan_guarded = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "models" / "guarded_ppo_v109").rglob("*.zip")
        if path.relative_to(ROOT).as_posix() not in referenced_guarded
    )
    if orphan_guarded:
        raise ValueError(f"Unreferenced guarded PPO checkpoint ZIPs are not allowed in candidate archive: {orphan_guarded}")
    for rel in sorted(IMMUTABLE_MODEL_ZIP_FILES):
        path = ROOT / rel
        if not path.exists():
            raise ValueError(f"Required immutable model ZIP is missing: {rel}")
    return required


def _initial_parent_model_path(branch: dict[str, Any]) -> Path | None:
    initialization = branch.get("initialization") or {}
    if initialization.get("mode") != "model":
        return None
    return ROOT / initialization["source_model_path"]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
