from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MECHANICS = ROOT / "data" / "mechanics" / "aemeath_mechanics.json"
FORTE = ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json"
AUDIT = ROOT / "data" / "source" / "aemeath_rupturous_trail_direct_audit_v98.json"
EXPECTED_AUDIT_SHA256 = "078e9bc31ea540c2b4441d9e2e14681f1cdd74db834a8358ce25b8c7f38a4094"
ACTION_SHEET = "\u89d2\u8272-\u5973"
OVERDRIVE_LABEL = "\u5927\u62db1"
GOOD_DAMAGE_REFS = ["dmg!2578", "dmg!2579", "dmg!2628", "dmg!2629"]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def trail_no_cost_text(mechanics: dict) -> str:
    for state in mechanics.get("states", []):
        if state.get("name") == "Trail No-cost":
            return "\n".join(state.get("modeled_behavior", []))
    raise AssertionError("Trail No-cost state not found")


def collect_c0_text(mechanics: dict, forte: dict) -> str:
    texts: list[str] = []
    texts.extend(mechanics.get("scope", {}).get("included", []))
    for state in mechanics.get("states", []):
        if state.get("name") in {"Trail No-cost", "Forte Enhancement"}:
            texts.append(state.get("name", ""))
            texts.extend(state.get("modeled_behavior", []))
    texts.extend(mechanics.get("forte_circuit", {}).get("modeled_behavior", []))
    texts.extend(mechanics.get("rupturous_trail", {}).get("modeled_behavior", []))
    for entry in mechanics.get("seraphic_duet", []):
        texts.append(entry.get("name", ""))
        texts.extend(entry.get("modeled_behavior", []))
    rupturous = forte["modes"]["tune_rupture"]["rupturous_trail"]
    for key, value in rupturous.items():
        if key != "source_refs":
            texts.append(str(value))
    for followup in forte["modes"]["tune_rupture"].get("seraphic_duet_followups", []):
        texts.append(followup.get("source_ref", ""))
        texts.append(followup.get("notes", ""))
        texts.extend(followup.get("confirmed_source_facts", []))
    return "\n".join(texts)


def assert_c0_values(section: dict) -> None:
    assert section["max_stacks"] == 30
    assert section["gain_per_trigger"] == 10
    assert section["duration_seconds"] == 30.0
    assert section["duration_clock"] == "combat_time"
    assert section["stack_bonus_per_stack"] == 0.04
    assert section["normal_repeat_count"] == 5
    assert section["enhanced_repeat_count"] == 10
    assert section["preservation_uses"] == 1


def main() -> None:
    assert [ord(c) for c in OVERDRIVE_LABEL] == [0x5927, 0x62DB, 0x0031]
    for path in [MECHANICS, FORTE]:
        data = path.read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf"), path
        data.decode("utf-8")

    mechanics = load(MECHANICS)
    forte = load(FORTE)
    audit = load(AUDIT)
    mechanic_section = mechanics["rupturous_trail"]
    forte_section = forte["modes"]["tune_rupture"]["rupturous_trail"]

    assert_c0_values(mechanic_section)
    assert_c0_values(forte_section)
    assert mechanic_section["source_refs"]["extra_tune_damage_rows"] == GOOD_DAMAGE_REFS
    assert forte_section["source_refs"]["extra_tune_damage_rows"] == GOOD_DAMAGE_REFS
    assert set(forte_section["source_refs"]["mechanic_rule"]) == {f"{ACTION_SHEET}!2844"}
    assert set(forte_section["source_refs"]["overdrive_preservation"]) == {f"{ACTION_SHEET}!2806"}
    assert set(forte_section["source_refs"]["seraphic_normal_action_rows"]) == {
        f"{ACTION_SHEET}!2786",
        f"{ACTION_SHEET}!2931",
    }
    assert set(forte_section["source_refs"]["seraphic_enhanced_action_rows"]) == {
        f"{ACTION_SHEET}!2787",
        f"{ACTION_SHEET}!2932",
    }

    combined_json = json.dumps([mechanics, forte], ensure_ascii=False)
    trail_text = trail_no_cost_text(mechanics)
    assert f"Granted by Overdrive / {OVERDRIVE_LABEL} for 30 seconds." in trail_text
    assert "???1" not in trail_text
    assert "\ufffd" not in combined_json
    bad_fragments = [
        "dmg/",
        "DamageData!2578",
        "DamageData!2579",
        "DamageData!2628",
        "DamageData!2629",
    ]
    assert not any(fragment in combined_json for fragment in bad_fragments), combined_json

    c0_text = collect_c0_text(mechanics, forte).lower()
    stale_phrases = [
        "scaffold",
        "scaffolding",
        "scaffold_only",
        "unresolved s0 trail removal",
        "unresolved runtime damage gate",
        "maximum stacks 5",
        "application unresolved",
        "consumption unresolved",
    ]
    assert not any(phrase in c0_text for phrase in stale_phrases), c0_text

    assert audit["direct_source_evidence"]["mechanic_rule"]["facts"][1] == "C0 maximum is 30 stacks."
    assert hashlib.sha256(AUDIT.read_bytes()).hexdigest() == EXPECTED_AUDIT_SHA256
    print("aemeath_rupturous_trail_metadata_exactness_smoke_test ok")


if __name__ == "__main__":
    main()
