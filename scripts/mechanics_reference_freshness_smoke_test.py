from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.mechanics_reference import load_mechanics_data


def _text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).lower()


def _load(character_id: str) -> dict[str, Any]:
    path = PROJECT_ROOT / "data" / "mechanics" / f"{character_id}_mechanics.json"
    assert path.exists(), f"missing mechanics file: {path}"
    with path.open("r", encoding="utf-8-sig") as file:
        raw = json.load(file)
    loaded = load_mechanics_data(character_id)
    assert loaded == raw, f"loader mismatch for {character_id}"
    return loaded


def main() -> None:
    aemeath = _load("aemeath")
    mornye = _load("mornye")

    aemeath_text = _text(aemeath)
    aemeath_excluded = _text(aemeath["scope"].get("excluded", []))
    for phrase in (
        "trailblazing star 5-set",
        "everbright polestar",
        "tune break",
        "starburst",
        "forte circuit",
        "seraphic duet follow-up",
        "source-gated generated mechanic damage",
        "1.0935",
        "forte enhancement",
    ):
        assert phrase in aemeath_text, f"Aemeath reference missing {phrase}"
    assert "trailblazing" not in aemeath_excluded, "Trailblazing Star should not be listed as excluded"
    assert "everbright" not in aemeath_excluded, "Everbright Polestar should not be listed as excluded"
    assert "starburst" not in aemeath_excluded, "Starburst should not be listed as excluded"
    assert "source-gated generated mechanic damage infrastructure" in _text(aemeath["scope"].get("included", []))
    assert aemeath["seraphic_duet_followup_damage"]["implementation_status"] == "implemented_workbook_confirmed"
    assert aemeath["seraphic_duet_followup_damage"]["source_status"] == "workbook_confirmed"
    assert aemeath["generated_mechanic_damage"]["implementation_status"] == "generic_runtime_infrastructure"
    assert "data/character_mechanic_effects/aemeath_forte_circuit.json" in _text(aemeath["forte_circuit"])
    assert "external simulator websites" in _text(aemeath["source_gated_implementation"])
    assert "fusion burst" in _text(aemeath["remaining_unresolved_mechanics"])
    assert "c6" in _text(aemeath["remaining_unresolved_mechanics"])
    assert "seraphic_duet_extra_tune_rupture_damage" not in aemeath_text
    assert "seraphic duet tune rupture follow-up damage is implemented" in aemeath_text

    mornye_text = _text(mornye)
    for phrase in (
        "halo of starry radiance",
        "starfield calibrator",
        "off-tune level",
        "tune break",
        "interfered marker",
        "particle jet",
        "high syntony field",
    ):
        assert phrase in mornye_text, f"Mornye reference missing {phrase}"

    interfered_text = _text(mornye["interfered_marker"])
    assert "tune_break_triggered" in interfered_text
    assert "simplified_on_inversion" in interfered_text
    assert "legacy" in interfered_text, "simplified_on_inversion should be described as legacy-only"
    assert "heavy inversion applies observation marker" in interfered_text
    assert "observation marker + mornye tune break applies interfered marker" in interfered_text

    limitations_text = _text(mornye["known_limitations"])
    assert "exact healing amount" in limitations_text
    assert "exact 3s heal tick timing" in limitations_text or "exact heal tick timing" in limitations_text
    assert "full multi-target marker tracking remains omitted" in limitations_text
    assert "current simulator implements excel-based single-target tune break" in limitations_text

    scope_included_text = _text(mornye["scope"].get("included", []))
    assert "full multi-target" not in scope_included_text

    assert "timing_model" in mornye
    timing_text = _text(mornye["timing_model"])
    assert "critical protocol / resonance liberation" in timing_text
    assert "combat_time_cost" in timing_text
    assert "global time stop" in timing_text
    assert "do not treat this as missing timing" in timing_text
    assert "unimplemented" not in timing_text.replace("not fully implemented", "")

    starfield_text = _text(mornye["weapons"])
    assert "starfield calibrator" in starfield_text
    assert "runtime_effects" in starfield_text
    assert "resonance skill concerto restore" in starfield_text
    assert "concerto energy" in starfield_text
    assert "party crit dmg on healing" in starfield_text
    assert "party crit dmg bonus" in starfield_text
    assert "weapon_base_attack" in starfield_text
    assert "def_percent_passive" in starfield_text
    assert "runtime_reapplied" in starfield_text
    assert "false" in starfield_text
    assert "interfered marker duration support" not in starfield_text

    everbright_text = _text(aemeath["weapons"])
    assert "everbright polestar" in everbright_text
    assert "runtime_effects" in everbright_text
    assert "all attribute dmg +12% at r1" in everbright_text
    assert "tune rupture - shifting / fusion burst" in everbright_text
    assert "8s resonance_liberation penetration buff" in everbright_text
    assert "def_ignore" in everbright_text
    assert "fusion_res_ignore" in everbright_text
    assert "formula modifiers, not damage bonuses" in everbright_text
    assert "not applied to tune break formula damage" in everbright_text
    assert "not applied to tune response formula damage" in everbright_text

    print("Mechanics reference freshness smoke test passed.")


if __name__ == "__main__":
    main()
