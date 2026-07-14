from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_completed_result import COMPLETED_DIR


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    summary = json.loads((root / COMPLETED_DIR / "winning_route_summary.json").read_text(encoding="utf-8"))
    refs = summary["comparison_against_references"]
    assert refs["manual_v114"]["total_damage"] == 5268418.084869607
    assert refs["current_reviewed_model_incumbent"]["total_damage"] == 5276844.358692044
    assert refs["historical_verified_bc"]["total_damage"] == 5165134.682363356
    assert refs["manual_v114"]["label"] == "current reviewed manual v114 reference"
    assert refs["current_reviewed_model_incumbent"]["label"] == "best trained model under the reviewed v114 runtime"
    assert "history only" in refs["historical_verified_bc"]["label"]
    assert summary["total_damage"] == 5651892.274552992
    assert summary["selected_sequence_sha256"] == "67a4250b3b8d0de9cec625448756226106ef0ed5134b8c4e4a0378518fa2f434"
    assert summary["resolved_sequence_sha256"] == "2b594e575203f29293b1f0e57ae51a07ff85d535ac957bde38a5911f6858c43a"
    print("beam_search_v116_route_reference_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
