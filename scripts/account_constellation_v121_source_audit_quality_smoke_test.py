from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_source_contract_v121 import CONTRACT
from account_constellation_source_workbook_v121 import load_source_cache
from account_constellation_v121_full_effect_mapping_completeness_smoke_test import validate_mappings


PLACEHOLDER = "Source-backed clause recorded in the cited workbook cell."
REFERENCE = re.compile(r"^[^!]+![A-Z]+[1-9][0-9]*(?::[A-Z]+[1-9][0-9]*)?$")


def main() -> None:
    path = ROOT / "data/source/user_account_constellation_single_boss_v121.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    workbook = source["workbook"]
    assert workbook["local_name"] == "wuthering_waves_action_data.xlsx"
    assert hashlib.sha256((ROOT / workbook["local_name"]).read_bytes()).hexdigest() == "81604978551989b5575e2d637ad4dfeb8c3b3b34d48e00a9ea79e9008c62f1f9"
    assert "sheet_refs" not in workbook
    assert all(REFERENCE.fullmatch(item["ref"]) for item in workbook["exact_cell_refs"])
    cache = load_source_cache(source)
    validate_mappings(source["effect_mappings"], cache)
    mappings = {mapping["effect_id"]: mapping for mapping in source["effect_mappings"]}
    assert all(mapping.get("exact_source_excerpt") != PLACEHOLDER for mapping in mappings.values())
    for effect_id, contract in CONTRACT.items():
        mapping = mappings[effect_id]
        if contract["source_type"] == "workbook_exact":
            assert all(REFERENCE.fullmatch(ref) for ref in mapping["sheet_cell_refs"])
        elif contract["source_type"] == "bwiki_exact":
            assert mapping["source_url"] == contract["url"] and mapping["access_date"]
        else:
            assert mapping["source_artifact"] == contract["artifact"]
    print("account_constellation_v121_source_audit_quality_smoke_test ok")


if __name__ == "__main__":
    main()
