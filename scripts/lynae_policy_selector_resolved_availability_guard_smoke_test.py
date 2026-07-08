from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
SELECTOR_ID = "lynae_resonance_liberation"
RESOLVED_ID = "lynae_resonance_liberation_prismatic_overblast"


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    sim.state.active_character_id = "lynae"
    assert sim.resolve_action_id(SELECTOR_ID) == RESOLVED_ID

    sim.state.resonance_energy["lynae"] = 0.0
    assert SELECTOR_ID not in sim.valid_action_ids()
    assert sim.is_action_available(sim.actions[SELECTOR_ID]) is False

    sim.state.resonance_energy["lynae"] = 125.0
    sim.state.cooldowns.pop("lynae_resonance_liberation", None)
    assert SELECTOR_ID in sim.valid_action_ids()
    assert sim.is_action_available(sim.actions[SELECTOR_ID]) is True

    assert sim.execute_action(SELECTOR_ID)
    assert SELECTOR_ID not in sim.valid_action_ids()
    assert sim.is_action_available(sim.actions[SELECTOR_ID]) is False

    print("lynae_policy_selector_resolved_availability_guard_smoke_test ok")


if __name__ == "__main__":
    main()
