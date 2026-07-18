from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from account_constellation_source_workbook_v121 import load_source_cache

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REFERENCE = re.compile(r"^[^!]+![A-Z]+[0-9]+(?::[A-Z]+[0-9]+)?$")


def main() -> None:
    source = json.loads((ROOT / "data/source/user_account_constellation_single_boss_v121.json").read_text(encoding="utf-8"))
    assert "sheet_refs" not in source["workbook"]
    references = [item["ref"] for item in source["workbook"].get("exact_cell_refs", [])]
    references.extend(ref for row in source["effect_mappings"] for ref in row.get("sheet_cell_refs", []))
    assert references and all(REFERENCE.fullmatch(ref) for ref in references)
    load_source_cache(source)
    assert not REFERENCE.fullmatch("\u89d2\u8272-\u5973!2844")
    print(f"account_constellation_v121_no_row_only_source_refs_smoke_test ok refs={len(references)}")


if __name__ == "__main__":
    main()
