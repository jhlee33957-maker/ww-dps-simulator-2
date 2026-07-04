from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def test_solo_aemeath_still_resolves() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath")
    assert sim.selected_party_character_ids == ["aemeath"]
    assert sim.execute_action("aemeath_basic_attack")
    row = sim.timeline[-1]
    assert row.selected_action_id == "aemeath_basic_attack"
    assert row.resolved_action_id == "aemeath_basic_form_stage_1"
    assert "aemeath" in row.mechanic_debug_after
    assert row.transition_type is None
    assert "concerto_ready" in sim.party_state.character_states["aemeath"]


def test_party_aemeath_still_resolves_while_active() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    assert sim.state.active_character_id == "aemeath"
    assert sim.execute_action("aemeath_basic_attack")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "aemeath_basic_form_stage_1"
    assert "aemeath" in sim.state.character_states
    assert sim.party_state.character_states["aemeath"]["form"] == sim.state.character_states["aemeath"]["form"]
    assert sim.party_state.character_states["aemeath"]["concerto_energy"] == sim.state.concerto_energy["aemeath"]
    assert row.actor_character_id == "aemeath"


def test_party_cutoff_still_clamps() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    sim.state.combat_time = 119.9
    assert sim.execute_action("aemeath_basic_attack")
    row = sim.timeline[-1]
    assert_close(sim.state.combat_time, 120.0, "party cutoff combat_time")
    assert row.truncated_by_combat_limit is True
    assert_close(row.effective_combat_time_cost, 0.1, "party cutoff effective cost")
    assert sim.execute_action("aemeath_basic_attack") is False


def main() -> None:
    test_solo_aemeath_still_resolves()
    test_party_aemeath_still_resolves_while_active()
    test_party_cutoff_still_clamps()
    print("Aemeath party integration smoke test passed.")


if __name__ == "__main__":
    main()
