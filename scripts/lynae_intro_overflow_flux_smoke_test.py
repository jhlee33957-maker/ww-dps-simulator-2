from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    sim.state.active_character_id = "aemeath"
    sim.state.concerto_energy["aemeath"] = 100.0
    assert sim.execute_action("swap_to_lynae")
    row = sim.state.action_log[-1]
    state = sim.state.character_mechanics_state["lynae"]
    assert row["incoming_intro_applied"] is True
    assert any(
        event.get("action_id") == "lynae_intro_time_to_show_some_colors"
        and event.get("applied")
        for event in row["transition_events"]
    )
    assert state["overflow"] == 100.0
    assert state["photocromic_flux_active"] is True
    assert sim.state.target_tune_shift_state == "tune_rupture_shifting"
    assert "lynae_intro_spectro_damage_bonus" in row["applied_buffs"]
    print("lynae_intro_overflow_flux_smoke_test ok")


if __name__ == "__main__":
    main()
