from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_source_workbook_v121 import load_source_cache
from account_constellation_source_contract_v121 import CONTRACT


CELL_REF_RE = re.compile(r"^([^!]+)!([A-Z]+[0-9]+)$")


def main() -> None:
    source = json.loads(
        (ROOT / "data" / "source" / "user_account_constellation_single_boss_v121.json").read_text(
            encoding="utf-8-sig"
        )
    )
    cache = load_source_cache(source)
    refs = source["workbook"].get("exact_cell_refs") or []
    assert len(refs) >= 8
    for item in refs:
        match = CELL_REF_RE.match(item["ref"])
        assert match, item["ref"]
        _sheet_name, _cell = match.groups()
        values = cache.get(item["ref"])
        assert any(value is not None for value in values), item["ref"]
        assert item["contains"] in " ".join(str(value) for value in values), (item["ref"], values, item["contains"])

    mappings = {mapping["effect_id"]: mapping for mapping in source["effect_mappings"]}
    for effect_id, contract in CONTRACT.items():
        mapping = mappings[effect_id]
        if contract["source_type"] == "workbook_exact":
            assert set(contract["refs"]).issubset(mapping["sheet_cell_refs"])

    for character_id in ("aemeath", "lynae", "mornye"):
        text = source["source_text"][character_id]
        assert "chinese" not in text
        assert text["source_backed_interpretation"]
        assert text["korean_interpretation"]
        assert text["english_interpretation"]
    print("account_constellation_v121_source_audit_cell_parity_smoke_test ok")


if __name__ == "__main__":
    main()
