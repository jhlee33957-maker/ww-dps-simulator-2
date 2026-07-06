from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def tune_ready(sim: Simulation) -> None:
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    sim.characters["mornye"].energy_regen = 2.7944
    sim.state.character_states["mornye"]["energy_regen"] = 2.7944
    sim.state.character_mechanics_state["mornye"]["mode"] = "wide_field_observation"
    sim.state.character_mechanics_state["mornye"]["relative_momentum"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    heavy_row = sim.timeline[-1]
    assert heavy_row.resolved_action_id == "mornye_heavy_inversion"
    assert heavy_row.observation_marker_applied is True
    assert heavy_row.mornye_interfered_marker_applied is False
    assert sim.state.interfered_marker_remaining == 0.0

    tune_ready(sim)
    assert sim.execute_action("mornye_tune_break")
    row = sim.timeline[-1]
    assert row.mornye_interfered_marker_applied is True
    assert row.interfered_marker_damage_taken_amp == 0.40
    assert row.interfered_marker_damage_taken_multiplier == 1.40
    assert row.interfered_marker_source == "observation_marker_tune_break"

    assert sim.execute_action("swap_to_aemeath")
    assert sim.execute_action("aemeath_basic_attack")
    amped = sim.timeline[-1].normal_damage
    baseline = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    baseline.state.active_character_id = "aemeath"
    assert baseline.execute_action("aemeath_basic_attack")
    assert amped > baseline.timeline[-1].normal_damage * 1.39

    assert sim.execute_action("swap_to_mornye")
    assert sim.execute_action("mornye_basic_attack")
    mornye_amped = sim.timeline[-1].normal_damage
    baseline_m = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    assert baseline_m.execute_action("mornye_basic_attack")
    assert mornye_amped > baseline_m.timeline[-1].normal_damage * 1.39

    sim.state.interfered_marker_remaining = 0.1
    assert sim.execute_action("short_wait")
    assert sim.summary().interfered_marker_remaining == 0.0

    no_obs = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    tune_ready(no_obs)
    assert no_obs.execute_action("mornye_tune_break")
    assert no_obs.timeline[-1].mornye_interfered_marker_applied is False

    legacy = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    legacy.state.mechanics_config["mornye"]["interfered_marker"]["mode"] = "simplified_on_inversion"
    legacy.state.character_mechanics_state["mornye"]["mode"] = "wide_field_observation"
    legacy.state.character_mechanics_state["mornye"]["relative_momentum"] = 100.0
    assert legacy.execute_action("mornye_heavy_attack")
    assert legacy.timeline[-1].interfered_marker_applied_by_simplified_inversion is True

    print("mornye_observation_interfered_marker_excel_flow_smoke_test ok")


if __name__ == "__main__":
    main()
