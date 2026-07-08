from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.source_ref_canonicalization import (
    CANONICAL_BOSS_COOLDOWN_SHEET,
    CANONICAL_BOSS_COOLDOWN_SOURCE_REF,
    CANONICAL_LYNAE_ACTION_SHEET,
    CANONICAL_LYNAE_SKILL_TYPE_SHEET,
    bad_markers,
)


def scan_paths() -> list[Path]:
    paths: set[Path] = set()
    paths.update((ROOT / "data").glob("*.json"))
    paths.update((ROOT / "data" / "mechanics").glob("*.json"))
    paths.update((ROOT / "data" / "extracted").glob("*.json"))
    paths.update((ROOT / "scripts").glob("*.py"))
    paths.update((ROOT / "reports").glob("*.md"))
    return sorted(path for path in paths if path.is_file() and path.suffix in {".json", ".py", ".md"})


def assert_no_bad_markers(text: str, path: Path, *, label: str) -> None:
    for marker in bad_markers():
        if marker in text:
            raise AssertionError(f"corrupt UTF-8 source ref marker {marker!r} found in {path} ({label})")


def main() -> None:
    required_ref_paths = [
        ROOT / "data" / "party_presets.json",
        ROOT / "data" / "transition_config.json",
    ]

    combined = ""
    for path in scan_paths():
        raw_text = path.read_text(encoding="utf-8")
        assert_no_bad_markers(raw_text, path, label="raw text")
        if path.suffix == ".json":
            data = json.loads(raw_text)
            text = json.dumps(data, ensure_ascii=False)
            if path in required_ref_paths:
                combined += text
                assert CANONICAL_BOSS_COOLDOWN_SOURCE_REF in text
            assert_no_bad_markers(text, path, label="decoded JSON")

    assert combined.count(CANONICAL_BOSS_COOLDOWN_SOURCE_REF) >= 3
    assert CANONICAL_BOSS_COOLDOWN_SHEET in combined

    source_audit = (ROOT / "scripts" / "lynae_source_audit.py").read_text(encoding="utf-8")
    assert CANONICAL_LYNAE_ACTION_SHEET in source_audit
    assert CANONICAL_LYNAE_SKILL_TYPE_SHEET in source_audit

    timing_json = json.loads((ROOT / "data" / "extracted" / "lynae_timing_cooldown_audit.json").read_text(encoding="utf-8"))
    assert CANONICAL_LYNAE_ACTION_SHEET in timing_json["source_region"]
    assert CANONICAL_LYNAE_SKILL_TYPE_SHEET in timing_json["skill_type_region"]

    print("lynae_utf8_source_ref_guard_smoke_test ok")


if __name__ == "__main__":
    main()
