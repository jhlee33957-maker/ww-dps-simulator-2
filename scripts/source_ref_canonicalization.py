from __future__ import annotations


CANONICAL_BOSS_COOLDOWN_SOURCE_REF = "\u9644\u98752!B227"
CANONICAL_BOSS_COOLDOWN_SHEET = "\u9644\u98752"
CANONICAL_LYNAE_ACTION_SHEET = "\u89d2\u8272-\u5973"
CANONICAL_LYNAE_SKILL_TYPE_SHEET = "\u89d2\u8272\u6280\u80fd\u7c7b\u578b"


def corrupt_boss_source_ref() -> str:
    return chr(0x3F) + chr(0xAFA6) + chr(0x3009) + "2!B227"


def corrupt_boss_source_sheet() -> str:
    return chr(0x3F) + chr(0xAFA6) + chr(0x3009) + "2"


def corrupt_boss_source_ref_prefix() -> str:
    return chr(0x3F) + chr(0xAFA6)


def corrupt_boss_source_ref_suffix() -> str:
    return chr(0x3009) + "2!B227"


def corrupt_escaped_boss_source_ref() -> str:
    return chr(0x5C) + chr(0x75) + "afa6" + chr(0x5C) + chr(0x75) + "30092!B227"


def corrupt_lynae_action_sheet_full() -> str:
    return chr(0x9C32) + chr(0xBBE6) + chr(0xB3EF) + "-" + chr(0x4E5F) + chr(0x3F)


def corrupt_lynae_skill_type_sheet_full() -> str:
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


def corrupt_lynae_sheet_prefix() -> str:
    return chr(0x9C32) + chr(0xBBE6) + chr(0xB3EF)


def corrupt_lynae_skill_type_marker() -> str:
    return chr(0xC379) + chr(0xAD73)


def bad_markers() -> list[str]:
    return [
        corrupt_boss_source_ref(),
        corrupt_boss_source_sheet(),
        corrupt_boss_source_ref_prefix(),
        corrupt_boss_source_ref_suffix(),
        corrupt_escaped_boss_source_ref(),
        corrupt_lynae_action_sheet_full(),
        corrupt_lynae_skill_type_sheet_full(),
        corrupt_lynae_sheet_prefix(),
        corrupt_lynae_skill_type_marker(),
    ]
