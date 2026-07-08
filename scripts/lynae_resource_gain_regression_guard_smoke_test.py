from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    actions = {action["id"]: action for action in json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))}
    alignment = json.loads(
        (ROOT / "data" / "extracted" / "lynae_resource_cooldown_alignment.json").read_text(encoding="utf-8")
    )
    records = {record["action_id"]: record for record in alignment["records"]}

    basic_1 = actions["lynae_basic_stage_1"]
    palette = actions["lynae_resonance_skill_palette"]
    overblast = actions["lynae_resonance_liberation_prismatic_overblast"]

    assert basic_1["resonance_energy_gain"] == 1.28
    assert basic_1["concerto_energy_gain"] == 4.59
    assert records["lynae_basic_stage_1"]["special_resource_gain"]["overflow_gain"] == 12.0
    assert palette["resonance_energy_gain"] == 8.75
    assert palette["concerto_energy_gain"] == 9.83
    assert records["lynae_resonance_skill_palette"]["special_resource_gain"]["overflow_gain"] == 25.0
    assert overblast["concerto_energy_gain"] == 20.0

    print("lynae_resource_gain_regression_guard_smoke_test ok")


if __name__ == "__main__":
    main()
