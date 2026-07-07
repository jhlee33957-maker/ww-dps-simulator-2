from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    assert set(sim.selected_character_ids) == {"aemeath", "lynae"}
    assert "mornye" not in sim.selected_character_ids
    assert sim.characters["aemeath"].build_profile_id == "aemeath_user_real_01"
    assert sim.characters["lynae"].build_profile_id == "lynae_user_real_01"
    assert "swap_to_lynae" in sim.get_policy_action_ids()
    assert "swap_to_aemeath" in sim.get_policy_action_ids()
    sim.state.concerto_energy["lynae"] = 100.0
    assert sim.execute_action("swap_to_aemeath")
    assert "lynae_outro_all_damage_amp" in sim.state.action_log[-1]["applied_buffs"]
    assert "mornye" not in sim.state.character_mechanics_state
    print("aemeath_lynae_party_integration_smoke_test ok")


if __name__ == "__main__":
    main()
