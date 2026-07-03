from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.extract_aemeath_qte_intro_outro import DEFAULT_OUTPUT, DEFAULT_REPORT, SOURCE_DIR, extract


def workbook_exists() -> bool:
    return SOURCE_DIR.exists() and any(SOURCE_DIR.glob("*.xlsx"))


def main() -> int:
    if not workbook_exists():
        print(
            "SKIP: no Excel workbook was found in data/source. "
            "Place an Aemeath source workbook there to run the QTE extraction smoke test."
        )
        return 0

    artifact = extract()
    assert DEFAULT_OUTPUT.exists(), f"Expected candidate JSON at {DEFAULT_OUTPUT}"
    assert DEFAULT_REPORT.exists(), f"Expected review markdown at {DEFAULT_REPORT}"

    loaded = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    assert loaded["review_status"] == "review_only_not_executable"
    assert "candidates" in loaded
    assert loaded["candidate_count"] == len(loaded["candidates"])
    assert loaded["candidate_count"] == artifact["candidate_count"]

    report = DEFAULT_REPORT.read_text(encoding="utf-8")
    for text in ("review-only", "not applied", "QTE", "?\uc107\uca95", "\uf978\ub739\uca95"):
        assert text in report, f"Review report should contain {text!r}"

    print("Aemeath QTE/Intro/Outro extraction smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
