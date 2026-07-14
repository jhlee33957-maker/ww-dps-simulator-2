from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_completed_result import (
    COMPLETED_DIR,
    CORE_HASHES,
    EXPECTED_FILE_COUNT,
    EXPECTED_TOTAL_BYTES,
    PLAN_SHA256,
    REVIEW_INVENTORY_ENTRY_DIGEST,
    WINNER_DAMAGE,
    WINNER_DPS,
    WINNER_ROUTE_ID,
    validate_compact_manifest,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = validate_compact_manifest(root)
    assert manifest["source_core_hashes"] == CORE_HASHES
    assert manifest["plan_sha256"] == PLAN_SHA256
    assert manifest["termination_status"] == "completed_search"
    completed = manifest["completed_search"]
    assert completed["expansions"] == 4908270
    assert completed["completed_bucket_count"] == 240
    assert completed["pending_buckets"] == []
    assert completed["completed_retained_route_count"] == 128
    assert manifest["winning_route"]["route_id"] == WINNER_ROUTE_ID
    assert manifest["winning_route"]["total_damage"] == WINNER_DAMAGE
    assert manifest["winning_route"]["dps"] == WINNER_DPS
    assert manifest["global_optimum_proven"] is False
    full = manifest["full_inventory"]
    assert full["file_count"] == EXPECTED_FILE_COUNT
    assert full["total_bytes"] == EXPECTED_TOTAL_BYTES
    assert full["normalized_entry_digest_sha256"] == REVIEW_INVENTORY_ENTRY_DIGEST
    routes = json.loads((root / COMPLETED_DIR / "completed_routes_compact.json").read_text(encoding="utf-8"))
    assert routes["route_count"] == 128
    assert routes["all_routes_completed_120s"] is True
    assert len({item["selected_sequence_sha256"] for item in routes["routes"]}) == 128
    assert len({item["resolved_sequence_sha256"] for item in routes["routes"]}) == 128
    print("beam_search_v116_completed_result_integrity_smoke_test ok")


if __name__ == "__main__":
    main()
