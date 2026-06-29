from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


EXPECTED_MULTIPLIERS = {
    "aemeath_basic_form_stage_1": [0.4635],
    "aemeath_basic_form_stage_2": [0.1389, 0.2084, 0.3473],
    "aemeath_basic_form_stage_3": [0.0932, 0.0932, 0.0932, 0.1863, 0.4656],
    "aemeath_basic_form_stage_4": [0.0673, 0.0673, 0.0673, 0.0673, 0.0673, 1.0094],
    "aemeath_mech_basic_stage_1": [0.232, 0.232, 0.232],
    "aemeath_mech_basic_stage_2": [0.1857, 0.7426],
    "aemeath_mech_basic_stage_3": [0.0389, 0.0389, 0.0389, 0.0389, 0.0389, 0.0389, 0.8154, 0.6165],
    "aemeath_mech_basic_stage_4": [0.4038, 0.9421],
    "aemeath_form_switch_to_mech": [0.2692, 0.4038, 0.6729],
    "aemeath_form_switch_to_aemeath": [0.1633, 0.1633, 0.1633, 1.1428],
    "aemeath_seraphic_duet_overturn": [
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
    ],
    "aemeath_seraphic_duet_encore": [0.179, 0.179, 0.179, 0.179, 0.3579, 0.3579, 0.3579, 1.7893],
    "aemeath_liberation_overdrive": [2.008, 2.6744, 2.6744, 2.6744],
    "aemeath_heavenfall_finale": [17.8929],
}


def main() -> None:
    actions = {
        action["id"]: action
        for action in json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))
    }

    for action_id, expected in EXPECTED_MULTIPLIERS.items():
        action = actions[action_id]
        actual = [hit["damage_multiplier"] for hit in action["hits"]]
        assert actual == expected, f"{action_id} multipliers: expected {expected}, got {actual}"
        print(f"{action_id}: {actual}")

    overdrive = actions["aemeath_liberation_overdrive"]
    assert overdrive["cooldown"] == 25
    assert overdrive["cooldown_group"] == "aemeath_overdrive"
    assert overdrive["resonance_energy_cost"] == 125
    assert overdrive["concerto_energy_gain"] == 20

    finale = actions["aemeath_heavenfall_finale"]
    assert finale["cooldown"] == 25
    assert finale["cooldown_group"] == "aemeath_finale"
    assert finale["resonance_energy_cost"] == 0
    assert finale["concerto_energy_gain"] == 20

    assert actions["aemeath_form_switch_to_mech"]["cooldown"] == 1
    assert actions["aemeath_form_switch_to_aemeath"]["cooldown"] == 1

    print("Aemeath coefficient smoke test passed.")


if __name__ == "__main__":
    main()
