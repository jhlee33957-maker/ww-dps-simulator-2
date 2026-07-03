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
VARIATION_DAMAGE = "\u53d8\u594f\u4f24\u5bb3"
RESONANCE_SKILL = "\u5171\u9e23\u6280\u80fd"
ALLOWED_EXECUTABLE_LABELS = {"QTE", "QTE-1", "QTE-2", "QTE-3"}
FORBIDDEN_EXECUTABLE_LABEL_PARTS = [
    "\u5f3a\u5316E",
    "\u5927\u62db1",
    "\u5927\u62db2",
    "\u7279\u6b8a\u80fd\u91cf",
    "\u8c10\u5ea6\u7834\u574f",
]


def workbook_exists() -> bool:
    return SOURCE_DIR.exists() and any(SOURCE_DIR.glob("*.xlsx"))


def _assert_candidate_scope(candidate: dict, expected_character: str) -> None:
    for bucket in ("source_rows", "executable_source_rows", "metadata_source_rows", "excluded_source_rows"):
        assert all(row["character"] == expected_character for row in candidate[bucket]), (
            f"{candidate['candidate_id']} mixes character scopes in {bucket}"
        )


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

    candidates = {candidate["candidate_id"]: candidate for candidate in payload["candidates"]}
    source_characters = {
        row["character"]
        for candidate in payload["candidates"]
        for row in candidate["source_rows"]
    }
    if {"aemeath", "aemeath_mech"}.issubset(source_characters):
        assert "aemeath_qte_intro_human" in candidates
        assert "aemeath_qte_intro_mech" in candidates

    for candidate in payload["candidates"]:
        assert "qte" in candidate["proposed_action_id"]
        assert candidate["simulation_executable"] is False
        assert candidate["policy_selectable"] is False
        expected_character = {
            "aemeath_qte_intro_human": "aemeath",
            "aemeath_qte_intro_mech": "aemeath_mech",
        }.get(candidate["candidate_id"])
        assert expected_character is not None, f"Unexpected candidate {candidate['candidate_id']}"
        _assert_candidate_scope(candidate, expected_character)

        damage = candidate["damage_candidate"]
        assert damage["parsed_multipliers"] or damage["warnings"]
        assert damage["raw_skill_category"] is not None
        assert damage["raw_skill_category_source_column"]
        assert damage["raw_damage_type"] is not None
        assert damage["raw_damage_type_source_column"]
        assert damage["raw_action_type"] is not None
        assert damage["raw_action_type_source_column"]
        assert damage["normalized_action_classification"] == "qte_intro"
        if VARIATION_DAMAGE in str(damage["raw_damage_type"]):
            assert damage["normalized_damage_category"] == "variation_damage"
        assert damage["qte_classification_confidence"] in {"high", "medium", "low"}

        executable_labels = [row["source_action_name"] or "" for row in candidate["executable_source_rows"]]
        assert set(executable_labels).issubset(ALLOWED_EXECUTABLE_LABELS)
        assert "QTE" in executable_labels
        assert any(label.startswith("QTE-") for label in executable_labels)
        for label in executable_labels:
            assert not any(forbidden in label for forbidden in FORBIDDEN_EXECUTABLE_LABEL_PARTS)
            assert not label.startswith("E1-QTE")

        followup_labels = [
            row["source_action_name"] or ""
            for row in candidate["notice_metadata"]["qte_followup_form_switch_notes"]
        ]
        assert followup_labels, "Expected E1-QTE follow-up notes to stay metadata-only"
        assert all(label.startswith("E1-QTE") for label in followup_labels)
        assert candidate["notice_metadata"]["previous_outro_trigger_frames"]

    if {"aemeath_qte_intro_human", "aemeath_qte_intro_mech"}.issubset(candidates):
        human_frames = candidates["aemeath_qte_intro_human"]["notice_metadata"]["previous_outro_trigger_frames"]
        mech_frames = candidates["aemeath_qte_intro_mech"]["notice_metadata"]["previous_outro_trigger_frames"]
        assert human_frames != mech_frames, "Previous Outro trigger frames should not be merged across sections"
        human_damage = candidates["aemeath_qte_intro_human"]["damage_candidate"]
        mech_damage = candidates["aemeath_qte_intro_mech"]["damage_candidate"]
        assert human_damage["normalized_action_classification"] == "qte_intro"
        assert human_damage["normalized_damage_category"] == "variation_damage"
        assert mech_damage["normalized_action_classification"] == "qte_intro"
        assert mech_damage["raw_skill_category"] is not None
        assert mech_damage["raw_damage_type"] is not None
        if mech_damage["raw_skill_category"] == RESONANCE_SKILL and mech_damage["raw_damage_type"] == VARIATION_DAMAGE:
            assert mech_damage["normalized_damage_category"] == "variation_damage"
            assert mech_damage["classification_warnings"], "Expected warning for mech raw category mismatch"
            assert candidates["aemeath_qte_intro_mech"]["safe_to_implement_later"] is False
            assert payload["classification_summary"]["raw_category_conflict_count"] >= 1

    sim = Simulation.from_json(DATA_DIR, party="aemeath")
    assert "aemeath_qte_intro_human" not in sim.get_policy_action_ids()
    assert "aemeath_qte_intro_mech" not in sim.get_policy_action_ids()
    assert all("qte" not in action_id.lower() for action_id in sim.get_policy_action_ids())

    report = DEFAULT_ACTION_CANDIDATE_REPORT.read_text(encoding="utf-8")
    for text in (
        "Classification Audit",
        "Raw skill category",
        "Raw damage type",
        "Normalized action",
        "Normalized damage",
        "Human QTE Candidate",
        "Cross-contamination check",
        "Executable candidates: 0",
        "simulation applied: false",
    ):
        assert text in report
    if "aemeath_qte_intro_mech" in candidates:
        assert "Mech QTE Candidate" in report
        if candidates["aemeath_qte_intro_mech"]["damage_candidate"]["classification_warnings"]:
            assert "candidate is classified as QTE by source label and damage type" in report
    assert "24 executable" not in report.lower()

    print("Aemeath QTE action candidate smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
