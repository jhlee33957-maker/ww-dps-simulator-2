from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.source_ref_canonicalization import (
    CANONICAL_BOSS_COOLDOWN_SHEET,
    CANONICAL_BOSS_COOLDOWN_SOURCE_REF,
    CANONICAL_LYNAE_ACTION_SHEET,
    CANONICAL_LYNAE_SKILL_TYPE_SHEET,
    bad_markers,
    corrupt_boss_source_ref,
    corrupt_boss_source_sheet,
    corrupt_escaped_boss_source_ref,
    corrupt_lynae_action_sheet_full,
    corrupt_lynae_skill_type_sheet_full,
)


TEXT_SUFFIXES = {".json", ".py", ".md"}


def scan_paths() -> list[Path]:
    paths: set[Path] = set()
    paths.update((ROOT / "data").glob("*.json"))
    paths.update((ROOT / "data" / "mechanics").glob("*.json"))
    paths.update((ROOT / "data" / "extracted").glob("*.json"))
    paths.update((ROOT / "scripts").glob("*.py"))
    paths.update((ROOT / "reports").glob("*.md"))
    return sorted(path for path in paths if path.is_file() and path.suffix in TEXT_SUFFIXES)


def replacements() -> list[tuple[str, str]]:
    return [
        (corrupt_boss_source_ref(), CANONICAL_BOSS_COOLDOWN_SOURCE_REF),
        (corrupt_boss_source_sheet(), CANONICAL_BOSS_COOLDOWN_SHEET),
        (corrupt_escaped_boss_source_ref(), CANONICAL_BOSS_COOLDOWN_SOURCE_REF),
        (corrupt_lynae_action_sheet_full(), CANONICAL_LYNAE_ACTION_SHEET),
        (corrupt_lynae_skill_type_sheet_full(), CANONICAL_LYNAE_SKILL_TYPE_SHEET),
    ]


def repair_text(text: str) -> str:
    repaired = text
    for old, new in replacements():
        repaired = repaired.replace(old, new)
    return repaired


def repair_files() -> None:
    for path in scan_paths():
        text = path.read_text(encoding="utf-8")
        repaired = repair_text(text)
        if repaired != text:
            path.write_text(repaired, encoding="utf-8")


def assert_clean() -> None:
    hits: list[tuple[str, str]] = []
    for path in scan_paths():
        text = path.read_text(encoding="utf-8")
        for marker in bad_markers():
            if marker in text:
                hits.append((str(path.relative_to(ROOT)), repr(marker)))
    if hits:
        for path, marker in hits:
            print(f"{path}: {marker}")
        raise SystemExit("corrupt source refs remain")


def main() -> None:
    repair_files()
    assert_clean()
    print("source-ref repair ok")


if __name__ == "__main__":
    main()
