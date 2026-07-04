from __future__ import annotations

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
        "actions",
        "outro",
        "intro",
        "syntony_field",
        "known_limitations",
    ):
        assert section in data, f"missing mechanics section: {section}"
        assert data[section], f"empty mechanics section: {section}"

    limitation_text = "\n".join(data["known_limitations"]).lower()
    assert "tune break is not implemented" in limitation_text
    assert "interfered marker is not implemented" in limitation_text
    assert any(row.get("action_id") == "mornye_outro_recursion" for row in data["outro"])
    assert any(row.get("action_id") == "mornye_intro_convergence" for row in data["intro"])

    print("Mornye mechanics reference smoke test passed.")


if __name__ == "__main__":
    main()
