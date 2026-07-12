from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHEET = "\u58f0\u9ab8"
EXPECTED_REFS = {
    f"{SOURCE_SHEET}!371",
    f"{SOURCE_SHEET}!383",
    f"{SOURCE_SHEET}!410",
    f"{SOURCE_SHEET}!411",
    f"{SOURCE_SHEET}!410:411",
}
TOUCHED_FILES = [
    ROOT / "data" / "actions.json",
    ROOT / "data" / "build_profiles.json",
    ROOT / "data" / "source" / "mornye_aemeath_active_echo_source_audit_v102.json",
    ROOT / "reports" / "mornye_aemeath_active_echo_source_audit.md",
    ROOT / "scripts" / "mornye_aemeath_active_echo_source_audit_smoke_test.py",
    ROOT / "scripts" / "project_progress_active_echo_alignment_smoke_test.py",
    ROOT / "simulator" / "simulation.py",
    ROOT / "PROJECT_PROGRESS_STATE.json",
]
BAD_CODEPOINT_SEQUENCE = [0x9DAF, 0xACC8, 0x3058]
BAD_ESCAPED = "\\u" + "9daf" + "\\u" + "acc8" + "\\u" + "3058"


def main() -> None:
    assert [ord(char) for char in SOURCE_SHEET] == [0x58F0, 0x9AB8]
    combined = ""
    for path in TOUCHED_FILES:
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"{path} has a UTF-8 BOM"
        text = raw.decode("utf-8")
        assert "\ufffd" not in text, f"{path} contains U+FFFD"
        codepoints = [ord(char) for char in text]
        for index in range(len(codepoints) - len(BAD_CODEPOINT_SEQUENCE) + 1):
            assert codepoints[index : index + len(BAD_CODEPOINT_SEQUENCE)] != BAD_CODEPOINT_SEQUENCE, (
                f"{path} contains stale U+9DAF/U+ACC8/U+3058 source text"
            )
        assert BAD_ESCAPED not in text.lower(), f"{path} contains stale escaped source sequence"
        combined += text
    for ref in EXPECTED_REFS:
        assert ref in combined, f"missing {ref}"
    audit_test = (ROOT / "scripts" / "mornye_aemeath_active_echo_source_audit_smoke_test.py").read_text(
        encoding="utf-8"
    )
    assert f"{SOURCE_SHEET}!383" in audit_test
    assert f"{SOURCE_SHEET}!410" in audit_test
    print("mornye_aemeath_active_echo_utf8_guard_smoke_test ok")


if __name__ == "__main__":
    main()
