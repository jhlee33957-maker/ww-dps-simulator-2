from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    sim.state.character_mechanics_state["lynae"]["overflow"] = 120.0
    assert sim.execute_action("lynae_spark_collision")
    for index in range(1, 4):
        assert sim.execute_action(f"lynae_polychrome_leap_stage_{index}")
    assert sim.execute_action("lynae_visual_impact")
    row = sim.state.action_log[-1]
    state = sim.state.character_mechanics_state["lynae"]
    assert row["lynae_photocromic_flux_applied"] is True
    assert row["lynae_visual_impact_tune_break_boost_buff_active"] is True
    assert row["lynae_visual_impact_tune_break_boost_value"] == 40.0
    assert "lynae_visual_impact_tune_break_boost" in row["applied_buffs"]
    assert state["true_color"] == 0.0
    assert state["spray_paint_window_remaining"] == 5.0
    assert state["visual_impact_cooldown_remaining"] > 0.0
    print("lynae_visual_impact_buff_flux_smoke_test ok")


if __name__ == "__main__":
    main()
