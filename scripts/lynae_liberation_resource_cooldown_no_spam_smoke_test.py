from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
SELECTOR_ID = "lynae_resonance_liberation"
RESOLVED_ID = "lynae_resonance_liberation_prismatic_overblast"
COOLDOWN_GROUP = "lynae_resonance_liberation"


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    sim.state.active_character_id = "lynae"
    sim.state.resonance_energy["lynae"] = 125.0

    assert sim.resolve_action_id(SELECTOR_ID) == RESOLVED_ID
    assert SELECTOR_ID in sim.valid_action_ids()
    assert sim.execute_action(SELECTOR_ID)
    row = sim.state.action_log[-1]
    assert row["selected_action_id"] == SELECTOR_ID
    assert row["resolved_action_id"] == RESOLVED_ID
    assert sim.state.resonance_energy["lynae"] < 125.0
    assert sim.state.cooldowns.get(COOLDOWN_GROUP, 0.0) > 0.0
    assert SELECTOR_ID not in sim.valid_action_ids()
    assert sim.execute_action(SELECTOR_ID) is False

    print("lynae_liberation_resource_cooldown_no_spam_smoke_test ok")


if __name__ == "__main__":
    main()
