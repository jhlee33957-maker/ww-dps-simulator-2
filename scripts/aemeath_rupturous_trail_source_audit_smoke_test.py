from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "078e9bc31ea540c2b4441d9e2e14681f1cdd74db834a8358ce25b8c7f38a4094"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    root_audit = ROOT / "aemeath_rupturous_trail_direct_audit_v98.json"
    source_copy = ROOT / "data" / "source" / "aemeath_rupturous_trail_direct_audit_v98.json"
    assert root_audit.exists()
    assert source_copy.exists()
    assert sha256(root_audit) == EXPECTED_SHA256
    assert sha256(source_copy) == EXPECTED_SHA256

    config = json.loads((ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json").read_text(encoding="utf-8"))
    trail = config["modes"]["tune_rupture"]["rupturous_trail"]
    assert trail["source_status"] == "workbook_confirmed_c0"
    assert trail["source_ref"] == "角色-女!2844"
    assert trail["gain_per_trigger"] == 10
    assert trail["max_stacks"] == 30
    assert trail["duration_clock"] == "combat_time"
    assert trail["base_multiplier_per_hit"] == 1.0935
    assert trail["normal_total_multiplier_by_stacks"]["at_30"] == 12.0285
    assert trail["enhanced_total_multiplier_by_stacks"]["at_30"] == 24.057
    print("aemeath_rupturous_trail_source_audit_smoke_test ok")


if __name__ == "__main__":
    main()
