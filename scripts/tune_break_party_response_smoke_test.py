from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def ready(sim: Simulation) -> None:
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    ready(sim)
    assert sim.execute_action("mornye_tune_break")
    row = sim.timeline[-1]
    assert row.party_response_scan_triggered is True
    assert row.aemeath_starburst_triggered is True
    assert row.mornye_particle_jet_triggered is True
    assert row.aemeath_starburst_damage_unresolved is True
    assert row.mornye_particle_jet_damage_unresolved is True
    assert "aemeath_starburst" in row.unresolved_response_damage_events
    assert "mornye_particle_jet" in row.unresolved_response_damage_events
    assert sim.summary().aemeath_starburst_trigger_count == 1
    assert sim.summary().mornye_particle_jet_trigger_count == 1

    ready(sim)
    assert sim.execute_action("mornye_tune_break")
    blocked = sim.timeline[-1]
    assert blocked.aemeath_starburst_cooldown_blocked is True
    assert blocked.mornye_particle_jet_cooldown_blocked is True

    print("tune_break_party_response_smoke_test ok")


if __name__ == "__main__":
    main()
