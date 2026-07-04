from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.mechanics_reference import load_mechanics_data


DATA_PATH = PROJECT_ROOT / "data" / "mechanics" / "mornye_mechanics.json"


def main() -> None:
    assert DATA_PATH.exists(), f"Missing mechanics data file: {DATA_PATH}"
    data = load_mechanics_data("mornye")
    for section in (
        "scope",
        "resources",
        "modes",
        "states",
        "actions",
        "energy_regen_scaling",
        "interfered_marker",
        "outro",
        "intro",
        "syntony_field",
        "known_limitations",
    ):
        assert section in data, f"missing mechanics section: {section}"
        assert data[section], f"empty mechanics section: {section}"

    limitation_text = "\n".join(data["known_limitations"]).lower()
    full_text = json.dumps(data, ensure_ascii=False).lower()
    scope_text = json.dumps(data["scope"], ensure_ascii=False).lower()
    states_text = json.dumps(data["states"], ensure_ascii=False).lower()
    energy_regen_text = json.dumps(data["energy_regen_scaling"], ensure_ascii=False).lower()
    interfered_marker_text = json.dumps(data["interfered_marker"], ensure_ascii=False).lower()
    resources_text = json.dumps(data["resources"], ensure_ascii=False).lower()

    assert "tune break" in full_text
    assert "not implemented" in limitation_text
    assert "full tune" in full_text
    assert "conversion" in full_text
    assert "full tune break" in limitation_text or "full tune break" in scope_text

    assert "interfered marker" in full_text
    assert "simplified" in interfered_marker_text
    assert "optional" in interfered_marker_text or "optional" in limitation_text
    assert "full tune" in interfered_marker_text
    assert "not implemented" in interfered_marker_text
    assert "game-client" in full_text or "full tune" in interfered_marker_text

    assert "energy regen" in full_text
    assert "decimal" in resources_text or "1.0 = 100%" in resources_text
    assert "2.6" in energy_regen_text or "2.60" in resources_text or "260" in energy_regen_text
    assert "support-test" in resources_text or "support-test" in full_text
    assert "mornye_liberation_critical_protocol" in energy_regen_text or "critical protocol" in energy_regen_text
    assert "crit rate" in energy_regen_text or "crit_rate" in energy_regen_text
    assert "crit dmg" in energy_regen_text or "crit_dmg" in energy_regen_text or "crit damage" in energy_regen_text
    assert "temporary" in energy_regen_text

    assert "damage_taken_amp" in interfered_marker_text or "dmg taken" in states_text
    assert "0.40" in interfered_marker_text or "40%" in interfered_marker_text
    assert "simplified_on_inversion" in interfered_marker_text
    assert "disabled" in interfered_marker_text
    assert any(row.get("action_id") == "mornye_outro_recursion" for row in data["outro"])
    assert any(row.get("action_id") == "mornye_intro_convergence" for row in data["intro"])

    print("Mornye mechanics reference smoke test passed.")


if __name__ == "__main__":
    main()
