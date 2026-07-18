from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import load_account_constellation_contract


DATA_DIR = ROOT / "data"
WORKBOOK_SHA256 = "81604978551989b5575e2d637ad4dfeb8c3b3b34d48e00a9ea79e9008c62f1f9"


def main() -> None:
    source = json.loads((DATA_DIR / "source" / "user_account_constellation_single_boss_v121.json").read_text(encoding="utf-8-sig"))
    contract = load_account_constellation_contract(DATA_DIR)
    assert source["baseline"]["latest_externally_verified_baseline"] == "120"
    assert source["workbook"]["sha256"] == WORKBOOK_SHA256
    assert source["workbook"]["exact_cell_refs"]
    assert hashlib.sha256((ROOT / "wuthering_waves_action_data.xlsx").read_bytes()).hexdigest() == WORKBOOK_SHA256
    assert source["scope"]["supported_scope"] == "single_persistent_boss_no_kill_no_survival"
    for character_id in ("aemeath", "lynae", "mornye"):
        character_source = source["source_text"][character_id]
        assert "chinese" not in character_source
        assert character_source["source_backed_interpretation"]
        assert character_source["korean_interpretation"]
        assert character_source["english_interpretation"]
    assert "Aemeath S5 all effects" in source["unsupported_effects"]
    assert contract["source_contract"] == "data/source/user_account_constellation_single_boss_v121.json"
    print("user_account_constellation_v121_source_contract_smoke_test ok")


if __name__ == "__main__":
    main()
