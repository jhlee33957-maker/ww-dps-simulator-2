from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from v124_timing_test_support import ROOT


HISTORICAL_SUMMARY = ROOT / "results/beam_search_v114_lowmem_10000_probe_summary.json"
EXPECTED_HISTORICAL_SUMMARY_SHA256 = "61e789992660dd49e9183c7f4e7306ceafb52d7eff5a2ee79ac24292bb78ecff"


def assert_historical_summary_hash(path: Path) -> None:
    assert path.is_file(), path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_HISTORICAL_SUMMARY_SHA256


def assert_one_byte_mutation_rejected() -> None:
    canonical = HISTORICAL_SUMMARY.read_bytes()
    mutated = bytearray(canonical)
    mutated[-1] ^= 1
    with tempfile.TemporaryDirectory(prefix="historical-summary-mutation-") as temporary:
        path = Path(temporary) / HISTORICAL_SUMMARY.name
        path.write_bytes(mutated)
        try:
            assert_historical_summary_hash(path)
        except AssertionError:
            return
    raise AssertionError("One-byte historical summary mutation was not rejected")


def main() -> None:
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    stage = progress["candidate_124_timing_core_1"]
    assert stage["historical_results_status"] == "preserved_but_requires_timing_rebaseline"
    assert stage["historical_result_files_rewritten"] is False
    assert_historical_summary_hash(HISTORICAL_SUMMARY)
    assert_one_byte_mutation_rejected()
    assert not any((ROOT / "results").glob("*v124*"))
    print(
        "historical_results_timing_rebaseline_status_v124_smoke_test ok "
        f"historical_sha256={EXPECTED_HISTORICAL_SUMMARY_SHA256} one_byte_mutation_rejected=true"
    )


if __name__ == "__main__":
    main()
