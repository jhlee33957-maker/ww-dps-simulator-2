from __future__ import annotations

import json
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    runpy.run_path(str(ROOT / "scripts/lynae_source_audit.py"), run_name="__main__")
    data = json.loads((ROOT / "data/extracted/lynae_source_audit.json").read_text(encoding="utf-8"))
    assert data["action_region"]["rows_found"] > 0
    assert data["damage_region"]["rows_found"] >= 80
    assert data["spectral_analysis"]["row"] == 2489
    assert abs(data["spectral_analysis"]["derived_multiplier"] - 18.8075) < 1e-9
    assert data["spectral_analysis_c2"]["row"] == 2490
    assert data["spectral_analysis_c2"]["implementation_status"] == "constellation_gated_disabled_by_default"
    classifications = {item["classification"] for item in data["findings"]}
    assert "workbook_confirmed" in classifications
    assert "user_supplied_tooltip" in classifications
    assert "user_profile" in classifications
    print("lynae_source_audit_smoke_test ok")


if __name__ == "__main__":
    main()
