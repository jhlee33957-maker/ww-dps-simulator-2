from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    inventories = json.loads((root / "results/mcts_v118_production_3x50k_v119/full_result_inventories.json").read_text(encoding="utf-8"))
    raw_present = True
    for seed in (118001, 118002, 118003):
        item = inventories["seeds"][str(seed)]
        assert item["raw_files_unchanged"] and item["core_hashes_before"] == item["core_hashes_after"]
        raw = root / item["result_root"] / "final_summary.json"
        if raw.is_file():
            assert json.loads(raw.read_text(encoding="utf-8"))["calibration_only"] is True
        else:
            raw_present = False
        derived = json.loads((root / f"results/mcts_v118_production_3x50k_v119/seed_{seed}/final_summary.json").read_text(encoding="utf-8"))
        assert derived["result_role"] == "production"
        assert derived["calibration_only"] is False and derived["production_search_result"] is True
    print(f"mcts_v118_production_metadata_correction_smoke_test ok raw_present={str(raw_present).lower()} raw_immutable=true derived=production")


if __name__ == "__main__": main()
