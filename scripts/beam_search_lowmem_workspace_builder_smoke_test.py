from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_lowmem_beam_workspace import REQUIRED_FILES, build_workspace
from scripts.build_lowmem_beam_result_archive import build_result_archive


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def fixture(root: Path) -> None:
    for relative in REQUIRED_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fixture:{relative}\n", encoding="utf-8")
    (root / "models/guarded_ppo_v109/checkpoint_1.zip").parent.mkdir(parents=True)
    (root / "models/guarded_ppo_v109/checkpoint_1.zip").write_bytes(b"heavy")
    (root / "results/guarded_ppo_v109/final_summary.json").parent.mkdir(parents=True)
    (root / "results/guarded_ppo_v109/final_summary.json").write_text("{}\n")
    (root / "__pycache__/cache.pyc").parent.mkdir()
    (root / "__pycache__/cache.pyc").write_bytes(b"cache")


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        source = base / "source"
        source.mkdir()
        fixture(source)
        before = tree_hash(source)
        first = build_workspace(source, base / "out1", apply=True)
        second = build_workspace(source, base / "out2", apply=True)
        assert tree_hash(source) == before
        assert first["manifest"] == second["manifest"]
        assert (base / "out1/search/beam_search.py").exists()
        assert (base / "out1/results/guarded_ppo_v109/final_summary.json").exists()
        assert not (base / "out1/models/guarded_ppo_v109/checkpoint_1.zip").exists()
        assert not list((base / "out1").rglob("*.pyc"))
        archived = build_result_archive(base / "out1", base / "result.zip")
        assert archived["entry_count"] > 0
        assert archived["cache_entry_count"] == 0
        try:
            build_workspace(source, source / "inside", apply=False)
        except ValueError:
            pass
        else:
            raise AssertionError("Builder accepted output inside source")
        nonempty = base / "nonempty"
        nonempty.mkdir()
        (nonempty / "x").write_text("x")
        try:
            build_workspace(source, nonempty, apply=True, overwrite_empty=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Builder accepted nonempty output")
    print("beam_search_lowmem_workspace_builder_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
