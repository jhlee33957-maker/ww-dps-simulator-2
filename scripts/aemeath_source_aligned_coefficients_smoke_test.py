from __future__ import annotations

import json
import math
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


EXPECTED_OVERDRIVE = [2.008, 2.6774, 2.6774, 2.6774]
EXPECTED_ENCORE = [0.179, 0.179, 0.3579, 0.3579, 0.179, 0.179, 1.7893, 0.3579]
EXPECTED_OVERTURN = [
    0.179,
    0.1492,
    0.1492,
    0.1492,
    0.1492,
    0.1492,
    0.1492,
    0.2386,
    0.2386,
    0.2386,
    0.5965,
    0.5965,
    0.5965,
]


def load_actions() -> dict[str, dict]:
    actions = json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))
    return {action["id"]: action for action in actions}


def multipliers(action: dict) -> list[float]:
    return [hit["damage_multiplier"] for hit in action["hits"]]


def assert_close(actual: float, expected: float, label: str) -> None:
    assert math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9), (
        f"{label}: expected {expected}, got {actual}"
    )


def assert_close_list(actual: list[float], expected: list[float], label: str) -> None:
    assert len(actual) == len(expected), f"{label}: expected {len(expected)} hits, got {len(actual)}"
    for index, (actual_value, expected_value) in enumerate(zip(actual, expected), start=1):
        assert_close(actual_value, expected_value, f"{label} hit {index}")


def assert_resources(action: dict, expected: dict[str, int]) -> None:
    for key, value in expected.items():
        assert action[key] == value, f"{action['id']} {key}: expected {value}, got {action[key]}"


def main() -> None:
    actions = load_actions()

    overdrive = actions["aemeath_liberation_overdrive"]
    assert_close_list(multipliers(overdrive), EXPECTED_OVERDRIVE, overdrive["id"])
    assert_close(overdrive["action_time"], 4.3667, "overdrive action_time")
    assert_close(overdrive["combat_time_cost"], 0.0, "overdrive combat_time_cost")
    assert_resources(
        overdrive,
        {
            "resonance_energy_cost": 125,
            "resonance_energy_gain": 0,
            "concerto_energy_gain": 20,
        },
    )
    assert overdrive["mechanic_effects"]["sync_delta"] == 30
    assert overdrive["mechanic_effects"]["resonance_rate_delta"] == 1
    assert overdrive["mechanic_effects"]["set_form"] == "mech"

    encore = actions["aemeath_seraphic_duet_encore"]
    assert_close_list(multipliers(encore), EXPECTED_ENCORE, encore["id"])
    assert_close(sum(multipliers(encore)), sum(EXPECTED_ENCORE), "encore total coefficient")
    assert_close(encore["action_time"], 2.4167, "encore action_time")
    assert_close(encore["combat_time_cost"], 1.3333, "encore combat_time_cost")
    assert_resources(
        encore,
        {
            "resonance_energy_cost": 0,
            "resonance_energy_gain": 8,
            "concerto_energy_gain": 10,
        },
    )
    assert encore["mechanic_effects"]["sync_delta"] == -100
    assert encore["mechanic_effects"]["resonance_rate_delta"] == 1
    assert encore["mechanic_effects"]["set_form"] == "aemeath"

    overturn_id = (
        "aemeath_seraphic_duet_overture"
        if "aemeath_seraphic_duet_overture" in actions
        else "aemeath_seraphic_duet_overturn"
    )
    assert_close_list(multipliers(actions[overturn_id]), EXPECTED_OVERTURN, overturn_id)
    assert_close_list(multipliers(actions["aemeath_heavenfall_finale"]), [17.8929], "aemeath_heavenfall_finale")

    print("Aemeath source-aligned coefficient smoke test passed.")


if __name__ == "__main__":
    main()
