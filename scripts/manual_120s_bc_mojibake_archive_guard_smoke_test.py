from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.manual_120s_bc_final_archive_integrity_smoke_test import (  # noqa: E402
    CORRECT_SHEET_NAME,
    FORBIDDEN_CORRUPTED_SHEET_NAME,
    scan_archive_text,
)


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        bad_zip = temp_root / "bad.zip"
        good_zip = temp_root / "good.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("data/actions.json", '{"source_sheet":"' + FORBIDDEN_CORRUPTED_SHEET_NAME + '"}')
        with zipfile.ZipFile(good_zip, "w") as zf:
            zf.writestr("data/actions.json", '{"source_sheet":"' + CORRECT_SHEET_NAME + '"}')
        with zipfile.ZipFile(bad_zip) as zf:
            bad_stats = scan_archive_text(zf, zf.namelist())
        with zipfile.ZipFile(good_zip) as zf:
            good_stats = scan_archive_text(zf, zf.namelist())
    assert bad_stats["forbidden_corrupted_sheet_occurrence_count"] == 1, bad_stats
    assert bad_stats["correct_sheet_occurrence_count"] == 0, bad_stats
    assert good_stats["forbidden_corrupted_sheet_occurrence_count"] == 0, good_stats
    assert good_stats["correct_sheet_occurrence_count"] == 1, good_stats
    assert good_stats["authoritative_correct_sheet_occurrence_count"] == 1, good_stats
    print("manual_120s_bc_mojibake_archive_guard_smoke_test ok")


if __name__ == "__main__":
    main()
