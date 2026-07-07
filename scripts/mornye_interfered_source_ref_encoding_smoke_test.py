from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.tune_break import INTERFERED_MARKER_AMP_SOURCE_REF, INTERFERED_MARKER_AMP_SOURCE_STATUS


EXPECTED_SOURCE_REF = "角色-女!4164"
EXPECTED_SOURCE_STATUS = "workbook_confirmed_row_4164"
MOJIBAKE_FRAGMENTS = (
    chr(0x9C32),
    chr(0xBBE6),
    chr(0xB3EF),
    chr(0x4E5F) + "?4164",
)
CHECKED_FILES = (
    ROOT / "simulator" / "tune_break.py",
    ROOT / "scripts" / "mornye_interfered_direct_damage_amp_smoke_test.py",
    ROOT / "scripts" / "mornye_interfered_liberation_damage_amp_smoke_test.py",
    ROOT / "scripts" / "mornye_interfered_event_order_smoke_test.py",
    ROOT / "data" / "mechanics" / "mornye_mechanics.json",
)


def main() -> None:
    assert INTERFERED_MARKER_AMP_SOURCE_REF == EXPECTED_SOURCE_REF
    assert INTERFERED_MARKER_AMP_SOURCE_STATUS == EXPECTED_SOURCE_STATUS
    for path in CHECKED_FILES:
        text = path.read_text(encoding="utf-8-sig")
        for fragment in MOJIBAKE_FRAGMENTS:
            assert fragment not in text, f"{fragment!r} remains in {path.relative_to(ROOT)}"
    print("mornye_interfered_source_ref_encoding_smoke_test ok")


if __name__ == "__main__":
    main()
