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


def main() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    policy_actions = sim.get_policy_action_ids()
    assert "swap_to_dummy_support" in policy_actions
    assert "swap_to_dummy_sub_dps" in policy_actions
    assert "swap_to_aemeath" in policy_actions
    assert not sim.is_action_available(sim.actions["swap_to_aemeath"])
    assert sim.is_action_available(sim.actions["swap_to_dummy_support"])

    assert sim.execute_action("swap_to_dummy_support")
    row = sim.timeline[-1]
    assert sim.state.active_character_id == "dummy_support"
    assert_close(sim.state.combat_time, 0.5, "swap combat_time")
    assert_close(row.action_time, 0.5, "swap action_time")
    assert_close(row.combat_time_cost, 0.5, "swap full combat cost")
    assert_close(row.effective_combat_time_cost, 0.5, "swap effective combat cost")
    assert row.actor_character_id == "aemeath"
    assert row.active_character_before == "aemeath"
    assert row.active_character_after == "dummy_support"
    assert row.outgoing_character_id == "aemeath"
    assert row.incoming_character_id == "dummy_support"
    assert row.fallback_swap_used is True
    assert row.swap_timing_is_placeholder is True
    assert row.swap_timing_source == "party_presets.aemeath_test_party.generic_swap"
    assert row.transition_events == []

    assert not sim.is_action_available(sim.actions["swap_to_dummy_support"])
    assert sim.is_action_available(sim.actions["dummy_support_attack"])
    assert sim.is_action_available(sim.actions["dummy_support_buff"])
    assert not sim.is_action_available(sim.actions["aemeath_basic_attack"])
    assert sim.is_action_available(sim.actions["swap_to_aemeath"])

    assert sim.execute_action("swap_to_aemeath")
    outro_row = sim.timeline[-1]
    assert_close(outro_row.action_time, 0.5, "outro fallback swap action_time")
    assert outro_row.outgoing_character_id == "dummy_support"
    assert outro_row.incoming_character_id == "aemeath"
    assert outro_row.outgoing_outro_event_id == "dummy_support_outro_damage_amp"
    assert outro_row.fallback_swap_used is True
    assert outro_row.swap_timing_is_placeholder is True
    assert "dummy_support_outro_damage_amp" in outro_row.applied_buffs

    print("Party swap smoke test passed.")


if __name__ == "__main__":
    main()
