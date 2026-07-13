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


DEFAULT_ARCHIVE = ROOT.parent / "ww-dps-simulator-2-111.zip"
STATE_PATH = ROOT / "results" / "guarded_ppo_v109" / "experiment_state.json"
EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", "bc_eval_bundle"}
IMMUTABLE_MODEL_ZIP_FILES = {
    "models/maskable_ppo_bc_v105.zip",
    "models/maskable_ppo_candidate_after_bc_v105.zip",
}


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
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(ROOT.rglob("*")):
            rel = path.relative_to(ROOT)
            parts = set(rel.parts)
            if path.is_dir():
                continue
            if path.resolve() == output:
                excluded_zip_count += 1
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
    }


def _required_zip_files_from_completed_state() -> set[str]:
    if not STATE_PATH.exists():
        raise ValueError(f"Completed guarded PPO state is required for candidate 111 archive: {STATE_PATH}")
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
