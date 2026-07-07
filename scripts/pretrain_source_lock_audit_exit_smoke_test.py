from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "pretrain_aemeath_mornye_source_lock_audit.py"
AUDIT_JSON = PROJECT_ROOT / "data" / "extracted" / "pretrain_aemeath_mornye_source_lock_audit.json"
AUDIT_REPORT = PROJECT_ROOT / "reports" / "pretrain_aemeath_mornye_source_lock_audit.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    try:
        result = subprocess.run(
            [sys.executable, str(AUDIT_SCRIPT)],
            cwd=PROJECT_ROOT,
            timeout=180,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            "pretrain source-lock audit did not exit within 180 seconds\n"
            f"stdout:\n{exc.stdout or ''}\n"
            f"stderr:\n{exc.stderr or ''}"
        ) from exc
    if result.returncode != 0:
        raise AssertionError(
            "pretrain source-lock audit failed\n"
            f"returncode={result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    assert "pretrain_aemeath_mornye_source_lock_audit" in result.stdout
    assert AUDIT_JSON.exists(), f"missing generated audit JSON: {AUDIT_JSON}"
    assert AUDIT_REPORT.exists(), f"missing generated audit report: {AUDIT_REPORT}"

    audit = load_json(AUDIT_JSON)
    assert audit["overall_status"] in {"PASS", "REVIEW_REQUIRED"}
    assert audit["source_confirmed_mismatches"] == []
    print("pretrain_source_lock_audit_exit_smoke_test ok")


if __name__ == "__main__":
    main()
