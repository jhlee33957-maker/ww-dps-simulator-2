from __future__ import annotations

import json
import math
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "source" / "direct_action_data_patch_manifest_v61.json"


def load_manifest_patches() -> dict[str, dict]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {patch["action_id"]: patch for patch in manifest["action_patches"]}


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


def assert_resources(action: dict, expected: dict[str, float]) -> None:
    for key, value in expected.items():
        assert_close(action[key], value, f"{action['id']} {key}")


def assert_manifest_alignment(action: dict, patch: dict) -> None:
    after = patch["after"]
    assert_close_list(multipliers(action), [float(after["damage_total"])], action["id"])
    assert_close(action["action_time"], after["action_time"], f"{action['id']} action_time")
    assert_close(action["combat_time_cost"], after["combat_time_cost"], f"{action['id']} combat_time_cost")
    assert_resources(
        action,
        {
            "resonance_energy_gain": float(after["resonance_energy_gain"]),
            "concerto_energy_gain": float(after["concerto_energy_gain"]),
        },
    )


def main() -> None:
    actions = load_actions()
    patches = load_manifest_patches()

    overdrive = actions["aemeath_liberation_overdrive"]
    assert_manifest_alignment(overdrive, patches[overdrive["id"]])
    assert_resources(
        overdrive,
        {
            "resonance_energy_cost": 125,
            "resonance_energy_gain": patches[overdrive["id"]]["after"]["resonance_energy_gain"],
            "concerto_energy_gain": patches[overdrive["id"]]["after"]["concerto_energy_gain"],
        },
    )
    assert overdrive["mechanic_effects"]["sync_delta"] == 30
    assert overdrive["mechanic_effects"]["resonance_rate_delta"] == 1
    assert overdrive["mechanic_effects"]["set_form"] == "mech"

    encore = actions["aemeath_seraphic_duet_encore"]
    assert_manifest_alignment(encore, patches[encore["id"]])
    assert_close(sum(multipliers(encore)), patches[encore["id"]]["after"]["damage_total"], "encore total coefficient")
    assert_resources(
        encore,
        {
            "resonance_energy_cost": 0,
            "resonance_energy_gain": patches[encore["id"]]["after"]["resonance_energy_gain"],
            "concerto_energy_gain": patches[encore["id"]]["after"]["concerto_energy_gain"],
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
    assert_manifest_alignment(actions[overturn_id], patches[overturn_id])
    assert_close_list(multipliers(actions["aemeath_heavenfall_finale"]), [17.8929], "aemeath_heavenfall_finale")

    print("Aemeath source-aligned coefficient smoke test passed.")


if __name__ == "__main__":
    main()
