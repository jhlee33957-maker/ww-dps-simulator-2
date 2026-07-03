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
    SOURCE_DIR,
    extract,
)
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"
FORBIDDEN_EXECUTABLE_LABEL_PARTS = [
    "强化E",
    "大招1",
    "大招2",
    "特殊能量",
    "谐度破坏",
]


def workbook_exists() -> bool:
    return SOURCE_DIR.exists() and any(SOURCE_DIR.glob("*.xlsx"))


def main() -> int:
    if not workbook_exists():
        print(
            "SKIP: no Excel workbook was found in data/source. "
            "Place an Aemeath source workbook there to run the QTE action candidate smoke test."
        )
        return 0

    before_actions = (DATA_DIR / "actions.json").read_text(encoding="utf-8-sig")
    extract()
    after_actions = (DATA_DIR / "actions.json").read_text(encoding="utf-8-sig")
    assert before_actions == after_actions, "Extraction must not modify data/actions.json"
    assert DEFAULT_ACTION_CANDIDATES_OUTPUT.exists()
    assert DEFAULT_ACTION_CANDIDATE_REPORT.exists()

    payload = json.loads(DEFAULT_ACTION_CANDIDATES_OUTPUT.read_text(encoding="utf-8"))
    assert payload["review_only"] is True
    assert payload["simulation_applied"] is False
    assert payload["simulation_executable"] is False
    assert payload["executable_policy_action_count"] == 0
    assert 1 <= payload["action_candidate_count"] <= 2

    candidate = payload["candidates"][0]
    assert "qte" in candidate["proposed_action_id"]
    assert candidate["simulation_executable"] is False
    assert candidate["policy_selectable"] is False
    assert "damage_candidate" in candidate
    damage = candidate["damage_candidate"]
    assert damage["parsed_multipliers"] or damage["warnings"]

    executable_labels = [row["source_action_name"] or "" for row in candidate["executable_source_rows"]]
    for label in ("QTE-1", "QTE-2", "QTE-3"):
        assert label in executable_labels
    for label in executable_labels:
        assert not any(forbidden in label for forbidden in FORBIDDEN_EXECUTABLE_LABEL_PARTS)
        assert not label.startswith("E1-QTE")

    followup_labels = [
        row["source_action_name"] or ""
        for row in candidate["notice_metadata"]["qte_followup_form_switch_notes"]
    ]
    assert any(label.startswith("E1-QTE") for label in followup_labels)
    assert candidate["notice_metadata"]["previous_outro_trigger_frames"]

    sim = Simulation.from_json(DATA_DIR, party="aemeath")
    assert "aemeath_qte_intro" not in sim.get_policy_action_ids()
    assert all("qte" not in action_id.lower() for action_id in sim.get_policy_action_ids())

    report = DEFAULT_ACTION_CANDIDATE_REPORT.read_text(encoding="utf-8")
    for text in (
        "Action Candidate Table",
        "Executable candidates: 0",
        "simulation applied: false",
        "QTE-1",
        "QTE-2",
        "QTE-3",
    ):
        assert text in report
    assert "24 executable" not in report.lower()

    print("Aemeath QTE action candidate smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
