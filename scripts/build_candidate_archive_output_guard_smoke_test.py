from __future__ import annotations

import zipfile
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_candidate_archive import build_archive  # noqa: E402


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        directory_output = temp_root / "archive_dir"
        directory_output.mkdir()
        try:
            build_archive(directory_output)
        except ValueError as exc:
            assert "directory" in str(exc)
            assert "ZIP file" in str(exc)
        else:
            raise AssertionError("directory output was not rejected")

        try:
            build_archive(ROOT)
        except ValueError as exc:
            assert "project root" in str(exc)
        else:
            raise AssertionError("project-root output was not rejected")

        output = temp_root / "candidate.zip"
        result = build_archive(output)
        assert output.exists()
        assert result["archive_path"] == output.as_posix()
        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
        name_set = set(names)
        expected_model_zips = {
            "models/maskable_ppo_bc_v105.zip",
            "models/maskable_ppo_candidate_after_bc_v105.zip",
            *[
                path.relative_to(ROOT).as_posix()
                for path in sorted(
                    (ROOT / "models" / "guarded_ppo_v109").glob("*/*.zip"),
                    key=lambda item: item.relative_to(ROOT).as_posix(),
                )
            ],
        }
        assert len(expected_model_zips) == 32
        assert expected_model_zips <= name_set
        assert "models/maskable_ppo_bc_v105.zip.bc_metadata.json" in name_set
        assert "models/maskable_ppo_candidate_after_bc_v105.zip.ppo_metadata.json" in name_set
        assert not any(name.startswith("/") or ":" in Path(name).parts[0] for name in names)
        assert not any("__pycache__" in Path(name).parts for name in names)
        assert not any(".pytest_cache" in Path(name).parts for name in names)
        assert not any(name.endswith((".pyc", ".pyo")) for name in names)
        assert not any(name.startswith("bc_eval_bundle/") for name in names)
        assert not any(name.endswith(".zip") and name not in expected_model_zips for name in names)
    print("build_candidate_archive_output_guard_smoke_test ok")


if __name__ == "__main__":
    main()
