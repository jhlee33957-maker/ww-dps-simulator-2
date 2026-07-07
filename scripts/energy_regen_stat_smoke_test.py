from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.models import CharacterData
from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, message: str, tolerance: float = 1e-6) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def test_character_energy_regen_default() -> None:
    character = CharacterData(id="missing_er", name="Missing ER", resonance_energy=0, concerto_energy=0)
    assert_close(character.energy_regen, 1.0, "Missing energy_regen should default to 1.0")


def test_resonance_energy_gain_only_scaling() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath")
    assert_close(sim.characters["aemeath"].energy_regen, 1.0, "Aemeath default ER")
    sim.characters["aemeath"].energy_regen = 2.0
    sim.state.character_states["aemeath"]["energy_regen"] = 2.0
    sim.state.resonance_energy["aemeath"] = 0.0

    assert sim.execute_action("aemeath_basic_attack"), "Aemeath basic should execute"
    row = sim.timeline[-1]
    assert_close(row.base_resonance_energy_gain, 5.0, "Base resonance gain should remain action value")
    assert_close(row.energy_regen, 2.0, "Timeline should log actor ER")
    assert_close(row.final_resonance_energy_gain, 10.0, "Final resonance gain should scale by ER")
    assert_close(row.resonance_energy_gained, 10.0, "Applied resonance gain should scale by ER")
    assert_close(row.concerto_gain, 4.0, "Concerto gain should not scale by ER")


def test_mornye_internal_resources_do_not_scale_with_energy_regen() -> None:
    sim = Simulation.from_json(DATA_DIR, party="mornye")
    assert_close(sim.characters["mornye"].energy_regen, 2.6, "Mornye support-test ER")

    assert sim.execute_action("mornye_basic_attack"), "Mornye baseline basic should execute"
    state = sim.state.character_states["mornye"]
    assert_close(state["rest_mass_energy"], 20.0, "Rest Mass Energy should not scale with ER")

    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 30.0
    state["relative_momentum"] = 0.0
    state["wfo_combo_stage"] = 1
    assert sim.execute_action("mornye_basic_attack"), "Mornye WFO basic should execute"
    assert_close(state["relative_momentum"], 10.0, "Relative Momentum should not scale with ER")


if __name__ == "__main__":
    test_character_energy_regen_default()
    test_resonance_energy_gain_only_scaling()
    test_mornye_internal_resources_do_not_scale_with_energy_regen()
    print("energy_regen_stat_smoke_test ok")
