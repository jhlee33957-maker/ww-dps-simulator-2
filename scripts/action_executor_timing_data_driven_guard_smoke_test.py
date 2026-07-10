from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXECUTOR_PATH = PROJECT_ROOT / "simulator" / "action_executor.py"


FORBIDDEN_ACTION_TIMING_BRANCH_IDS = (
    "aemeath_tune_break",
    "mornye_liberation_critical_protocol",
    "lynae_kaleidoscopic_basic_stage_1",
)

FORBIDDEN_NUMERIC_TIMINGS = (
    r"94\s*/\s*60",
    r"296\s*/\s*60",
    r"40\s*/\s*60",
)


def main() -> None:
    source = EXECUTOR_PATH.read_text(encoding="utf-8")
    for action_id in FORBIDDEN_ACTION_TIMING_BRANCH_IDS:
        assert action_id not in source, f"executor must not branch timing on {action_id}"
    for pattern in FORBIDDEN_NUMERIC_TIMINGS:
        assert not re.search(pattern, source), f"executor must not duplicate timing constant {pattern}"


if __name__ == "__main__":
    main()
