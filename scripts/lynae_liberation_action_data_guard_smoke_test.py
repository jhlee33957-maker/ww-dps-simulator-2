from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    actions = {action["id"]: action for action in json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))}

    selector = actions["lynae_resonance_liberation"]
    overblast = actions["lynae_resonance_liberation_prismatic_overblast"]

    assert selector["damage_multiplier"] == 0
    assert selector["data_status"] == "non_damaging_selector"
    assert selector["resonance_energy_cost"] == 125
    assert selector["cooldown"] == 25
    assert selector["cooldown_group"] == "lynae_resonance_liberation"

    assert overblast["resonance_energy_cost"] == 125
    assert overblast["cooldown"] == 25
    assert overblast["cooldown_group"] == "lynae_resonance_liberation"
    assert overblast["action_time"] == 4.0
    assert overblast["combat_time_cost"] == 0.0
    assert {2692, 2693, 2695, 2482}.issubset(set(overblast["source_rows"]))
    assert "workbook_confirmed_global_timestop" in overblast["source_status"]
    assert "decision_frame_240F" in overblast["source_status"]
    assert "damage_repeat_from_2695" in overblast["source_status"]
    assert "299F is the timed-combat duration" not in overblast.get("notes", "")

    c5 = actions.get("lynae_resonance_liberation_prismatic_overblast_c5")
    if c5 is not None:
        assert c5["resonance_energy_cost"] == 125
        assert c5["cooldown"] == 25
        assert c5["cooldown_group"] == "lynae_resonance_liberation"
        assert c5["action_time"] == 4.0
        assert c5["combat_time_cost"] == 0.0

    print("lynae_liberation_action_data_guard_smoke_test ok")


if __name__ == "__main__":
    main()
