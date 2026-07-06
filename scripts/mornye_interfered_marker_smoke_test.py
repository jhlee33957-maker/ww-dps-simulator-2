from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
BUFF_ID = "mornye_interfered_marker_damage_amp"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


def assert_close(actual: float, expected: float, message: str, tolerance: float = 1e-6) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def prep_inversion(sim: Simulation) -> None:
    state = sim.state.character_states["mornye"]
    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 30.0
    state["relative_momentum"] = 100.0
    state["wfo_combo_stage"] = 1
    sim.state.active_character_id = "mornye"


def find_marker(sim: Simulation):
    return next((buff for buff in sim.state.active_buffs if buff.buff_id == BUFF_ID), None)


def make_config_with_marker_mode(mode: str) -> dict:
    config = deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("mornye", {}).setdefault("interfered_marker", {})["mode"] = mode
    return config


def test_marker_disabled_by_default() -> None:
    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["mornye", "aemeath"])
    prep_inversion(sim)
    assert sim.execute_action("mornye_heavy_attack"), "Heavy Inversion should execute"
    row = sim.timeline[-1]
    assert row.resolved_action_id == "mornye_heavy_inversion", "Heavy should resolve to Inversion"
    assert row.mornye_interfered_marker_mode == "disabled", "Default marker mode should be disabled"
    assert row.mornye_interfered_marker_applied is False, "Disabled marker should not apply"
    assert find_marker(sim) is None, "Disabled mode should not create marker buff"


def test_marker_dry_run_logs_without_applying() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_test_party", transition_config=make_config_with_marker_mode("dry_run"))
    prep_inversion(sim)
    assert sim.execute_action("mornye_heavy_attack"), "Heavy Inversion should execute"
    row = sim.timeline[-1]
    assert row.mornye_interfered_marker_mode == "dry_run", "Dry-run marker mode"
    assert_close(row.mornye_interfered_amp or 0.0, 0.40, "Dry-run should log marker amp potential")
    assert row.mornye_interfered_marker_applied is False, "Dry-run should not apply marker"
    assert find_marker(sim) is None, "Dry-run should not create marker buff"


def test_simplified_marker_applies_refreshes_and_amps_party_damage() -> None:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        transition_config=make_config_with_marker_mode("simplified_on_inversion"),
    )
    assert (
        sim.transition_config["mechanics"]["mornye"]["interfered_marker"]["mode"] == "simplified_on_inversion"
    ), "Legacy simplified marker mode should be explicit"
    assert (
        sim.transition_config["mechanics"]["mornye"]["mornye_expectation_error_mode"] == "expectation_error_only"
    ), "Enabled test party should not silently force Mornye Optimal Solution"

    prep_inversion(sim)
    assert sim.execute_action("mornye_heavy_attack"), "Heavy Inversion should execute"
    first_row = sim.timeline[-1]
    marker = find_marker(sim)
    assert marker is not None, "Simplified mode should create marker buff"
    assert first_row.mornye_interfered_marker_applied is True, "Timeline should log marker apply"
    assert BUFF_ID in first_row.applied_buffs, "Timeline should include marker buff id"
    assert_close(float(marker.metadata["dynamic_value"]), 0.40, "Marker dynamic amp value")
    assert_close(marker.remaining_duration, 30.0, "Marker should start at configured duration")

    sim.state.active_character_id = "aemeath"
    assert sim.execute_action("aemeath_basic_attack"), "Aemeath basic should execute under marker"
    marker_damage = sim.timeline[-1].normal_damage

    baseline = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        transition_config=make_config_with_marker_mode("simplified_on_inversion"),
    )
    baseline.state.active_character_id = "aemeath"
    assert baseline.execute_action("aemeath_basic_attack"), "Baseline Aemeath basic should execute"
    baseline_damage = baseline.timeline[-1].normal_damage
    assert marker_damage > baseline_damage * 1.39, "Marker should amp nearby party damage by about 40%"

    prep_inversion(sim)
    assert sim.execute_action("mornye_heavy_attack"), "Second Heavy Inversion should refresh marker"
    markers = [buff for buff in sim.state.active_buffs if buff.buff_id == BUFF_ID]
    assert len(markers) == 1, "Marker should refresh without stacking"
    assert_close(markers[0].remaining_duration, 30.0, "Marker refresh should restore duration")
    assert_close(float(markers[0].metadata["dynamic_value"]), 0.40, "Marker refresh should keep computed value")


if __name__ == "__main__":
    test_marker_disabled_by_default()
    test_marker_dry_run_logs_without_applying()
    test_simplified_marker_applies_refreshes_and_amps_party_damage()
    print("mornye_interfered_marker_smoke_test ok")
