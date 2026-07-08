from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import source_ref_canonicalization as c


def expected_corrupt_boss_source_ref() -> str:
    return chr(0x3F) + chr(0xAFA6) + chr(0x3009) + "2!B227"


def expected_corrupt_boss_source_sheet() -> str:
    return chr(0x3F) + chr(0xAFA6) + chr(0x3009) + "2"


def expected_corrupt_boss_source_ref_prefix() -> str:
    return chr(0x3F) + chr(0xAFA6)


def expected_corrupt_boss_source_ref_suffix() -> str:
    return chr(0x3009) + "2!B227"


def expected_corrupt_escaped_boss_source_ref() -> str:
    return chr(0x5C) + chr(0x75) + "afa6" + chr(0x5C) + chr(0x75) + "30092!B227"


def expected_corrupt_lynae_action_sheet_full() -> str:
    return chr(0x9C32) + chr(0xBBE6) + chr(0xB3EF) + "-" + chr(0x4E5F) + chr(0x3F)


def expected_corrupt_lynae_skill_type_sheet_full() -> str:
    return (
        chr(0x9C32)
        + chr(0xBBE6)
        + chr(0xB3EF)
        + chr(0x3F)
        + chr(0x80)
        + chr(0x3F)
        + chr(0xC379)
        + chr(0xAD73)
        + chr(0x3F)
        + chr(0x3F)
    )


def expected_corrupt_lynae_sheet_prefix() -> str:
    return chr(0x9C32) + chr(0xBBE6) + chr(0xB3EF)


def expected_corrupt_lynae_skill_type_marker() -> str:
    return chr(0xC379) + chr(0xAD73)


def expected_bad_markers() -> list[str]:
    return [
        expected_corrupt_boss_source_ref(),
        expected_corrupt_boss_source_sheet(),
        expected_corrupt_boss_source_ref_prefix(),
        expected_corrupt_boss_source_ref_suffix(),
        expected_corrupt_escaped_boss_source_ref(),
        expected_corrupt_lynae_action_sheet_full(),
        expected_corrupt_lynae_skill_type_sheet_full(),
        expected_corrupt_lynae_sheet_prefix(),
        expected_corrupt_lynae_skill_type_marker(),
    ]


def main() -> None:
    assert c.CANONICAL_BOSS_COOLDOWN_SOURCE_REF == "\u9644\u98752!B227"
    assert c.CANONICAL_BOSS_COOLDOWN_SHEET == "\u9644\u98752"
    assert c.CANONICAL_LYNAE_ACTION_SHEET == "\u89d2\u8272-\u5973"
    assert c.CANONICAL_LYNAE_SKILL_TYPE_SHEET == "\u89d2\u8272\u6280\u80fd\u7c7b\u578b"

    assert c.corrupt_boss_source_ref() == expected_corrupt_boss_source_ref()
    assert c.corrupt_boss_source_sheet() == expected_corrupt_boss_source_sheet()
    assert c.corrupt_boss_source_ref_prefix() == expected_corrupt_boss_source_ref_prefix()
    assert c.corrupt_boss_source_ref_suffix() == expected_corrupt_boss_source_ref_suffix()
    assert c.corrupt_escaped_boss_source_ref() == expected_corrupt_escaped_boss_source_ref()
    assert c.corrupt_lynae_action_sheet_full() == expected_corrupt_lynae_action_sheet_full()
    assert c.corrupt_lynae_skill_type_sheet_full() == expected_corrupt_lynae_skill_type_sheet_full()
    assert c.corrupt_lynae_sheet_prefix() == expected_corrupt_lynae_sheet_prefix()
    assert c.corrupt_lynae_skill_type_marker() == expected_corrupt_lynae_skill_type_marker()
    assert c.bad_markers() == expected_bad_markers()

    source = (ROOT / "scripts" / "source_ref_canonicalization.py").read_text(encoding="utf-8")
    for marker in expected_bad_markers():
        assert marker not in source, repr(marker)

    print("source_ref_canonicalization_self_guard_smoke_test ok")


if __name__ == "__main__":
    main()
