from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.mechanics_reference import load_mechanics_data


DATA_PATH = PROJECT_ROOT / "data" / "mechanics" / "aemeath_mechanics.json"


def approx(actual: float, expected: float, tolerance: float = 1e-4) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def main() -> None:
    assert DATA_PATH.exists(), f"Missing mechanics data file: {DATA_PATH}"
    with DATA_PATH.open("r", encoding="utf-8-sig") as file:
        raw_data = json.load(file)

    loaded_data = load_mechanics_data("aemeath")
    assert loaded_data == raw_data
    assert loaded_data["character_id"] == "aemeath"

    required_keys = {
        "scope",
        "resources",
        "states",
        "action_resolution_priority",
        "timing_model",
        "form_switch",
        "heavy_attack",
        "sync_strike",
        "seraphic_duet",
        "overdrive_finale",
        "sync_delta_table",
        "known_limitations",
    }
    missing = required_keys - set(loaded_data)
    assert not missing, f"Missing top-level keys: {sorted(missing)}"

    timing_names = {row["name"] for row in loaded_data["timing_model"]}
    for expected_name in (
        "Overdrive",
        "Finale",
        "Seraphic Duet Encore",
        "Sync Strike Armament Merge",
        "Human Charged II",
        "Instant Response Human Charged II",
    ):
        assert expected_name in timing_names, f"Missing timing model row: {expected_name}"

    sync_deltas = {row["name"]: row.get("sync_delta") for row in loaded_data["sync_delta_table"]}
    expected_sync_deltas = {
        "Human Basic 4": 23.31,
        "Mech Basic 4": 23.28,
        "Armament Merge": 18.29,
        "Call of Dawn": 22.18,
        "Overdrive": 30,
    }
    for name, expected in expected_sync_deltas.items():
        assert name in sync_deltas, f"Missing sync_delta row: {name}"
        assert_approx = approx(float(sync_deltas[name]), float(expected))
        assert assert_approx, f"{name} sync_delta expected {expected}, got {sync_deltas[name]}"

    assert loaded_data["known_limitations"], "known_limitations should not be empty"
    print("Aemeath mechanics reference smoke test passed.")


if __name__ == "__main__":
    main()
