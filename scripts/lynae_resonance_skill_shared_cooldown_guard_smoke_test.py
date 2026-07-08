from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_lynae_enabled_test_party"
SELECTOR_ID = "lynae_resonance_skill"
PALETTE_ID = "lynae_resonance_skill_palette"
ADDITIVE_ID = "lynae_resonance_skill_additive_color"
COOLDOWN_GROUP = "lynae_resonance_skill"


def main() -> None:
    actions = {action["id"]: action for action in json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))}
    selector = actions[SELECTOR_ID]
    palette = actions[PALETTE_ID]
    additive = actions[ADDITIVE_ID]

    assert selector["cooldown"] == 6.0
    assert selector["cooldown_group"] == COOLDOWN_GROUP
    assert selector["source_status"] == "non_damaging_selector_resolved_shared_cooldown"
    assert palette["cooldown"] == 6.0
    assert additive["cooldown"] == 6.0
    assert palette["cooldown_group"] == COOLDOWN_GROUP
    assert additive["cooldown_group"] == COOLDOWN_GROUP
    assert palette["source_status"] == "user_confirmed_numeric_cooldown"
    assert additive["source_status"] == "user_confirmed_numeric_cooldown"
    assert palette["action_time"] == 1.1
    assert palette["combat_time_cost"] == 1.1
    assert additive["action_time"] == 0.9167
    assert additive["combat_time_cost"] == 0.9167

    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    sim.state.active_character_id = "lynae"
    assert SELECTOR_ID in sim.valid_action_ids()
    assert sim.resolve_action_id(SELECTOR_ID) == PALETTE_ID
    assert sim.execute_action(SELECTOR_ID)
    assert sim.state.action_log[-1]["resolved_action_id"] == PALETTE_ID
    assert sim.state.cooldowns[COOLDOWN_GROUP] == 6.0
    assert SELECTOR_ID not in sim.valid_action_ids()
    assert sim.is_resolved_action_available(sim.actions[ADDITIVE_ID]) is False

    for _ in range(12):
        assert sim.execute_action("short_wait")

    assert sim.state.cooldowns.get(COOLDOWN_GROUP, 0.0) <= 0.0
    assert SELECTOR_ID in sim.valid_action_ids()

    print("lynae_resonance_skill_shared_cooldown_guard_smoke_test ok")


if __name__ == "__main__":
    main()
