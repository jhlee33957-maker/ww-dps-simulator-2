from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.roster import read_party_presets


def main() -> None:
    party = read_party_presets(ROOT / "data")["aemeath_mornye_lynae_account_actual_01"]
    assert party["display_name"] == "Aemeath S6 / Mornye S3 / Lynae S2 Account Actual"
    assert party["configuration_status"] == "Stored and configuration-ready"
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    for text in (
        "Stored and configuration-ready",
        "Aemeath mode:",
        "Precombat:",
        "Initial active:",
        'account_summary["baseline"]',
    ):
        assert text in app_text
    assert party["account_ui_summary"]["baseline"] == "No account baseline has been executed"
    print("account_party_v122_ui_visibility_smoke_test ok")


if __name__ == "__main__":
    main()
