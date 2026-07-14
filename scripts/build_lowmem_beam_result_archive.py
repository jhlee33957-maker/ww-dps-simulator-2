from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_result_archive(workspace: Path, output: Path) -> dict[str, object]:
    workspace = workspace.resolve()
    output = output.resolve()
    if output == workspace or workspace in output.parents:
        raise ValueError("Result archive output must be outside the runtime workspace")
    if not (workspace / "LOWMEM_WORKSPACE_MANIFEST.json").exists():
        raise ValueError("LOWMEM_WORKSPACE_MANIFEST.json is required")
    output.parent.mkdir(parents=True, exist_ok=True)
    entry_count = 0
    cache_entry_count = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in workspace.rglob("*") if item.is_file()):
            relative = path.relative_to(workspace)
            if set(relative.parts) & EXCLUDED_DIRS or path.suffix in {".pyc", ".pyo"}:
                cache_entry_count += 1
                continue
            if path.suffix == ".zip":
                continue
            archive.write(path, relative.as_posix())
            entry_count += 1
    return {
        "archive_path": output.as_posix(),
        "archive_sha256": sha256_file(output),
        "entry_count": entry_count,
        "cache_entry_count": cache_entry_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a cache-free post-run archive from a slim Beam workspace.")
    parser.add_argument("--workspace", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_result_archive(args.workspace, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
