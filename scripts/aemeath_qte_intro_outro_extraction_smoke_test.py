from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.extract_aemeath_qte_intro_outro import (
    DEFAULT_ACTION_CANDIDATE_REPORT,
    DEFAULT_ACTION_CANDIDATES_OUTPUT,
    DEFAULT_OUTPUT,
    DEFAULT_REPORT,
    SOURCE_DIR,
    extract,
)
from simulator.simulation import Simulation


def workbook_exists() -> bool:
    return SOURCE_DIR.exists() and any(SOURCE_DIR.glob("*.xlsx"))


def main() -> int:
    if not workbook_exists():
        print(
            "SKIP: no Excel workbook was found in data/source. "
            "Place an Aemeath source workbook there to run the QTE extraction smoke test."
        )
        return 0

    artifact = extract()
    assert DEFAULT_OUTPUT.exists(), f"Expected candidate JSON at {DEFAULT_OUTPUT}"
    assert DEFAULT_REPORT.exists(), f"Expected review markdown at {DEFAULT_REPORT}"
    assert DEFAULT_ACTION_CANDIDATES_OUTPUT.exists(), f"Expected action candidate JSON at {DEFAULT_ACTION_CANDIDATES_OUTPUT}"
    assert DEFAULT_ACTION_CANDIDATE_REPORT.exists(), f"Expected action candidate report at {DEFAULT_ACTION_CANDIDATE_REPORT}"

    loaded = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    assert loaded["review_only"] is True
    assert loaded["simulation_applied"] is False
    assert loaded["candidate_count"] == len(loaded["candidates"])
    assert loaded["candidate_count"] == artifact["candidate_count"]
    assert loaded["raw_candidate_row_count"] == loaded["candidate_count"]
    assert loaded["action_candidate_count"] >= 1
    assert loaded["executable_candidate_count"] == 0
    assert loaded["action_candidate_output"].endswith("aemeath_qte_action_candidates.json")
    assert loaded["candidate_count"] > 0
    assert loaded["candidate_count"] < 100
    assert any("qte" in group["group_id"] for group in loaded["groups"])
    action_payload = json.loads(DEFAULT_ACTION_CANDIDATES_OUTPUT.read_text(encoding="utf-8"))
    assert action_payload["action_candidate_count"] in {1, 2}
    assert action_payload["executable_policy_action_count"] == 0
    assert {
        candidate["candidate_id"] for candidate in action_payload["candidates"]
    }.issubset({"aemeath_qte_intro_human", "aemeath_qte_intro_mech"})

    for group in loaded["groups"]:
        for row in group["source_rows"]:
            assert row["character"] in {"aemeath", "aemeath_mech"}
            assert row["character"] != "other"

    report = DEFAULT_REPORT.read_text(encoding="utf-8")
    for text in (
        "Aemeath QTE",
        "review_only",
        "simulation_applied = false",
        "previous-character outro",
        "split by human/mech",
    ):
        assert text in report, f"Review report should contain {text!r}"
    assert len(report.splitlines()) < 180, "Review report should stay compact."

    sim = Simulation.from_json(PROJECT_ROOT / "data", party="aemeath")
    assert all("qte" not in action_id.lower() for action_id in sim.get_policy_action_ids())

    print("Aemeath QTE/Intro/Outro extraction smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
