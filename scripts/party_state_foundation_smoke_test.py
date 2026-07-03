from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.models import PartyState
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def assert_party_state(sim: Simulation, members: list[str], active: str) -> None:
    party_state = sim.party_state
    assert isinstance(party_state, PartyState)
    assert party_state.party_members == members
    assert party_state.active_character_id == active
    assert set(party_state.character_states) == set(members)
    assert party_state.combat_time == 0.0
    assert party_state.current_time == 0.0
    assert party_state.combat_duration == sim.combat_duration
    assert party_state.total_damage == 0.0
    assert party_state.team_buffs == []
    assert party_state.damage_log == []
    assert party_state.action_log == []
    assert party_state.cooldowns == {}


def main() -> None:
    solo = Simulation.from_json(DATA_DIR, party="aemeath")
    assert_party_state(solo, ["aemeath"], "aemeath")
    assert "aemeath" in solo.state.character_states

    test_party = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    assert_party_state(
        test_party,
        ["aemeath", "dummy_support", "dummy_sub_dps"],
        "aemeath",
    )
    assert "aemeath" in test_party.state.character_states
    assert "dummy_support" in test_party.state.character_states
    assert "dummy_sub_dps" in test_party.state.character_states

    print("Party state foundation smoke test passed.")


if __name__ == "__main__":
    main()
