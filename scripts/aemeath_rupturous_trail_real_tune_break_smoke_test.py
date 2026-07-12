from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0
    assert sim.execute_action("mornye_tune_break")
    row = sim.timeline[-1]
    assert row.party_response_scan_triggered is True
    assert row.aemeath_starburst_triggered is True
    assert row.mornye_particle_jet_triggered is True
    assert row.lynae_spectral_analysis_triggered is True
    assert len(row.aemeath_rupturous_trail_gain_events) == 3
    assert sim.state.rupturous_trail_stacks == 30
    assert sim.state.rupturous_trail_event_log[-1]["stacks_after"] == 30
    print("aemeath_rupturous_trail_real_tune_break_smoke_test ok")


if __name__ == "__main__":
    main()
