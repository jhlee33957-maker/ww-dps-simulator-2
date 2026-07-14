from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_completed_result import (
    COMPLETED_INVENTORY_PATH,
    EXPECTED_FILE_COUNT,
    EXPECTED_TOTAL_BYTES,
    HEAVY_OUTPUT,
    REVIEW_INVENTORY_ENTRY_DIGEST,
    inventory_entry_digest,
    validate_inventory,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    inventory = json.loads((root / COMPLETED_INVENTORY_PATH).read_text(encoding="utf-8"))
    assert inventory["file_count"] == len(inventory["files"]) == EXPECTED_FILE_COUNT
    assert inventory["total_bytes"] == sum(item["bytes"] for item in inventory["files"]) == EXPECTED_TOTAL_BYTES
    assert inventory["normalized_entry_digest_sha256"] == REVIEW_INVENTORY_ENTRY_DIGEST
    assert inventory_entry_digest(inventory["files"]) == REVIEW_INVENTORY_ENTRY_DIGEST
    heavy = root / HEAVY_OUTPUT
    if heavy.is_dir():
        validated = validate_inventory(heavy, inventory)
        assert validated["file_count"] == EXPECTED_FILE_COUNT
        assert validated["total_bytes"] == EXPECTED_TOTAL_BYTES
    else:
        print("heavy completed result absent; compact 1,051-entry inventory contract validated only")
    print("beam_search_v116_completed_inventory_smoke_test ok")


if __name__ == "__main__":
    main()
