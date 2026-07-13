from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


CHECKED_PATHS = (
    ROOT / "results" / "manual_120s_bc_demonstration_v105_summary.json",
    ROOT / "reports" / "manual_120s_bc_demonstration_v105.md",
    ROOT / "PROJECT_PROGRESS_STATE.json",
)
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/]"),
    re.compile(r"\\\\Users\\\\", re.IGNORECASE),
    re.compile(r"/Users/", re.IGNORECASE),
)


def main() -> None:
    for path in CHECKED_PATHS:
        data = path.read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf"), f"{path} has a UTF-8 BOM"
        text = data.decode("utf-8")
        assert "\ufffd" not in text, f"{path} contains replacement characters"
        for pattern in ABSOLUTE_PATH_PATTERNS:
            assert not pattern.search(text), f"{path} contains a machine-specific absolute path"
    summary = json.loads(CHECKED_PATHS[0].read_text(encoding="utf-8"))
    assert summary["dataset_path"] == "data/generated/manual_120s_bc_demonstration_v105.npz"
    assert not Path(summary["dataset_path"]).is_absolute()
    print("manual_120s_bc_report_portability_smoke_test ok")


if __name__ == "__main__":
    main()
