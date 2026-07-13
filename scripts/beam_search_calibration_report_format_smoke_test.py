from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "beam_search_v111_calibration_results.md"


def main() -> None:
    raw = REPORT.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    lines = raw.decode("utf-8").splitlines()
    assert lines[0] == "# Beam Search v111 30-second calibration result"
    prefixes = ("+##", "+- ", "+Candidate", "+The ")
    assert not any(line.startswith(prefixes) for line in lines), [line for line in lines if line.startswith("+")]
    assert any(line == "## Completion" for line in lines)
    assert any(line.startswith("- Plan:") for line in lines)
    print("beam_search_calibration_report_format_smoke_test ok")


if __name__ == "__main__":
    main()
