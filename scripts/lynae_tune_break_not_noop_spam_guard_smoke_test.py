from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


ACTION_ID = "lynae_tune_break"


def main() -> None:
    sim = Simulation.from_json(
        ROOT / "data",
        party="aemeath_lynae_enabled_test_party",
        initial_active_character="lynae",
    )
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max
    assert ACTION_ID in sim.valid_action_ids()

    assert sim.execute_action(ACTION_ID)
    row = sim.timeline[-1]
    assert row.tune_break_damage > 0.0
    assert row.enemy_tune_break_cooldown_started is True
    assert row.enemy_tune_break_cooldown_remaining == 3.0
    assert row.enemy_tune_break_available is False
    assert row.enemy_mistune_active is False
    assert row.enemy_off_tune_current_after_tune_break == 0.0

    assert sim.state.enemy_tune_break_available is False
    assert sim.state.enemy_mistune_active is False
    assert sim.state.enemy_off_tune_current == 0.0
    assert sim.state.enemy_tune_break_cooldown_remaining == 3.0
    assert ACTION_ID not in sim.valid_action_ids()
    assert sim.execute_action(ACTION_ID) is False
    assert len(sim.timeline) == 1

    print("lynae_tune_break_not_noop_spam_guard_smoke_test ok")


if __name__ == "__main__":
    main()
