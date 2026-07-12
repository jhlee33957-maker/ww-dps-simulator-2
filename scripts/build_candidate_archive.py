from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT.parent / "ww-dps-simulator-2(106).zip"
EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", "bc_eval_bundle"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}


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
    if output.exists():
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
            if path.suffix == ".zip":
                excluded_zip_count += 1
                continue
            zf.write(path, rel.as_posix())
            entry_count += 1
    return {
        "archive_path": output.as_posix(),
        "archive_sha256": _sha256(output),
        "entry_count": entry_count,
        "excluded_cache_count": excluded_cache_count,
        "excluded_zip_count": excluded_zip_count,
        "excluded_venv_git_or_bundle_count": excluded_venv_or_git_count,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
