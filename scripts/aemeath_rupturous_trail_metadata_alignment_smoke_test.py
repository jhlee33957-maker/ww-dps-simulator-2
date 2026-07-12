from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MECHANICS = ROOT / "data" / "mechanics" / "aemeath_mechanics.json"
FORTE = ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json"
AUDIT = ROOT / "data" / "source" / "aemeath_rupturous_trail_direct_audit_v98.json"
EXPECTED_AUDIT_SHA256 = "078e9bc31ea540c2b4441d9e2e14681f1cdd74db834a8358ce25b8c7f38a4094"
ACTION_SHEET = "\u89d2\u8272-\u5973"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def assert_no_personal_rupturous_fields(fields: list[str]) -> None:
    blocked = {
        "rupturous_trail_stacks",
        "rupturous_trail_remaining",
        "rupturous_trail_max_stacks",
    }
    assert not blocked.intersection(fields), fields


def main() -> None:
    mechanics = load_json(MECHANICS)
    forte = load_json(FORTE)

    section = mechanics["rupturous_trail"]
    assert section["implementation_status"] == "implemented_workbook_confirmed_c0_pending_external_review"
    assert section["source_status"] == "workbook_confirmed_c0"
    assert section["max_stacks"] == 30
    assert section["gain_per_trigger"] == 10
    assert section["duration_seconds"] == 30.0
    assert section["stack_bonus_per_stack"] == 0.04
    assert "CombatState.rupturous_trail_stacks" in section["state_fields"]
    assert "CombatState.rupturous_trail_remaining" in section["state_fields"]
    assert_no_personal_rupturous_fields(section["state_fields"])
    assert section["debug_fields"] == [
        "target_rupturous_trail_stacks",
        "target_rupturous_trail_remaining",
        "target_rupturous_trail_max_stacks",
    ]

    stale_text = "\n".join(
        mechanics.get("scope", {}).get("excluded", [])
        + mechanics.get("remaining_unresolved_mechanics", [])
        + mechanics.get("known_limitations", [])
    )
    assert "Rupturous Trail source-confirmed stack" not in stale_text
    assert "Fusion Trail / Rupturous Trail stack state is scaffolded" not in stale_text

    rupturous = forte["modes"]["tune_rupture"]["rupturous_trail"]
    assert rupturous["owner_state"] == "CombatState.rupturous_trail_stacks"
    assert rupturous["remaining_state"] == "CombatState.rupturous_trail_remaining"
    assert rupturous["legacy_personal_state"] == "ignored_removed"
    assert rupturous["gain_per_trigger"] == 10
    assert rupturous["max_stacks"] == 30
    assert rupturous["duration_seconds"] == 30.0
    assert rupturous["stack_bonus_per_stack"] == 0.04
    assert set(rupturous["source_refs"]["seraphic_normal_action_rows"]) == {
        f"{ACTION_SHEET}!2786",
        f"{ACTION_SHEET}!2931",
    }
    assert set(rupturous["source_refs"]["seraphic_enhanced_action_rows"]) == {
        f"{ACTION_SHEET}!2787",
        f"{ACTION_SHEET}!2932",
    }
    assert f"{ACTION_SHEET}!2806" in rupturous["source_refs"]["overdrive_preservation"]
    assert f"{ACTION_SHEET}!2844" in rupturous["source_refs"]["mechanic_rule"]
    assert any("2578" in ref for ref in rupturous["source_refs"]["extra_tune_damage_rows"])
    assert any("2579" in ref for ref in rupturous["source_refs"]["extra_tune_damage_rows"])
    assert any("2628" in ref for ref in rupturous["source_refs"]["extra_tune_damage_rows"])
    assert any("2629" in ref for ref in rupturous["source_refs"]["extra_tune_damage_rows"])

    import hashlib

    assert hashlib.sha256(AUDIT.read_bytes()).hexdigest() == EXPECTED_AUDIT_SHA256
    print("aemeath_rupturous_trail_metadata_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
