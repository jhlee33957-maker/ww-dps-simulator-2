from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_production_result import COMPACT_RESULT, PLAN_SHA256, SEEDS, load_compact_inventories, validate_all, validate_compact


def main() -> None:
    compact = validate_compact(ROOT)
    inventories = load_compact_inventories(ROOT)
    assert compact["manifest"]["plan_sha256"] == PLAN_SHA256
    full = __import__("json").loads((ROOT / COMPACT_RESULT / "full_result_inventories.json").read_text(encoding="utf-8"))
    for seed, expected in SEEDS.items():
        item = full["seeds"][str(seed)]
        assert item["file_count"] == 22 and item["total_bytes"] == expected["total_bytes"]
        assert item["normalized_inventory_digest_sha256"] == expected["inventory_digest"]
        assert item["core_hashes_before"] == item["core_hashes_after"] == expected["core_hashes"]
        assert item["raw_files_unchanged"] is True
    raw_present = all((ROOT / full["seeds"][str(seed)]["result_root"]).is_dir() for seed in SEEDS)
    if raw_present:
        validated = validate_all(ROOT, inventories=inventories, replay=False)
        assert sum(len(item["leaderboard"]["routes"]) for item in validated["seeds"].values()) == 384
    assert compact["aggregate"]["global_optimum_proven"] is False
    print(f"mcts_v118_3x50k_integrity_smoke_test ok raw_present={str(raw_present).lower()} files=66 routes=384")


if __name__ == "__main__": main()
