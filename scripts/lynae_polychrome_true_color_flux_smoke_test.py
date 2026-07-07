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
        assert sim.state.action_log[-1]["lynae_photocromic_flux_applied"] is True
    state = sim.state.character_mechanics_state["lynae"]
    assert state["lumiflow"] == 0.0
    assert state["true_color"] == 3.0
    assert state["photocromic_flux_active"] is True
    assert sim.state.target_tune_shift_state == "tune_rupture_shifting"
    print("lynae_polychrome_true_color_flux_smoke_test ok")


if __name__ == "__main__":
    main()
