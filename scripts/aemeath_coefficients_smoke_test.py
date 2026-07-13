from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "source" / "direct_action_data_patch_manifest_v61.json"


EXPECTED_ACTION_IDS = [
    "aemeath_basic_form_stage_1",
    "aemeath_basic_form_stage_2",
    "aemeath_basic_form_stage_3",
    "aemeath_basic_form_stage_4",
    "aemeath_mech_basic_stage_1",
    "aemeath_mech_basic_stage_2",
    "aemeath_mech_basic_stage_3",
    "aemeath_mech_basic_stage_4",
    "aemeath_form_switch_to_mech_normal",
    "aemeath_form_switch_to_aemeath_normal",
    "aemeath_form_switch_to_aemeath_after_overdrive",
    "aemeath_sync_strike_armament_merge",
    "aemeath_sync_strike_call_of_dawn",
    "aemeath_seraphic_duet_overturn",
    "aemeath_seraphic_duet_encore",
    "aemeath_heavy_aemeath_charged_1",
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_1",
    "aemeath_heavy_mech_charged_2",
    "aemeath_liberation_overdrive",
    "aemeath_heavenfall_finale",
]


def manifest_damage_totals() -> dict[str, list[float]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    patches = {patch["action_id"]: patch for patch in manifest["action_patches"]}
    return {action_id: [float(patches[action_id]["after"]["damage_total"])] for action_id in EXPECTED_ACTION_IDS}


def main() -> None:
    actions = {
        action["id"]: action
        for action in json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))
    }

    for action_id, expected in manifest_damage_totals().items():
        action = actions[action_id]
        actual = [hit["damage_multiplier"] for hit in action["hits"]]
        assert actual == expected, f"{action_id} multipliers: expected {expected}, got {actual}"
        print(f"{action_id}: {actual}")

    overdrive = actions["aemeath_liberation_overdrive"]
    assert overdrive["cooldown"] == 25
    assert overdrive["cooldown_group"] == "aemeath_overdrive"
    assert overdrive["resonance_energy_cost"] == 125
    assert overdrive["concerto_energy_gain"] == 20
    assert overdrive["mechanic_effects"]["sync_delta"] == 30
    assert overdrive["mechanic_effects"]["resonance_rate_delta"] == 1

    finale = actions["aemeath_heavenfall_finale"]
    assert finale["cooldown"] == 25
    assert finale["cooldown_group"] == "aemeath_finale"
    assert finale["resonance_energy_cost"] == 0
    assert finale["concerto_energy_gain"] == 20
    assert finale["mechanic_effects"]["set_synchronization_rate"] == 0
    assert finale["mechanic_effects"]["set_resonance_rate"] == 0

    assert actions["aemeath_form_switch_to_mech_normal"]["cooldown"] == 1
    assert actions["aemeath_form_switch_to_aemeath_normal"]["cooldown"] == 1
    assert actions["aemeath_form_switch_to_aemeath_after_overdrive"]["cooldown"] == 1
    assert actions["aemeath_form_switch_to_mech_normal"]["cooldown_group"] == "aemeath_form_switch"
    assert actions["aemeath_form_switch_to_aemeath_normal"]["cooldown_group"] == "aemeath_form_switch"
    assert actions["aemeath_form_switch_to_aemeath_after_overdrive"]["cooldown_group"] == "aemeath_form_switch"
    assert actions["aemeath_sync_strike_armament_merge"]["cooldown_group"] != "aemeath_form_switch"
    assert actions["aemeath_sync_strike_call_of_dawn"]["cooldown_group"] != "aemeath_form_switch"

    print("Aemeath coefficient smoke test passed.")


if __name__ == "__main__":
    main()
