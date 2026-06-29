from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def aemeath_state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["aemeath"]


def run_step(sim: Simulation, selected_action_id: str, expected_resolved_id: str | None = None) -> str:
    resolved_id = sim.resolve_action_id(selected_action_id)
    print(f"Selected {selected_action_id} -> resolved {resolved_id}")
    if expected_resolved_id is not None:
        assert resolved_id == expected_resolved_id, f"Expected {expected_resolved_id}, got {resolved_id}"
    ok = sim.execute_action(selected_action_id)
    assert ok, f"Failed to execute {selected_action_id} resolved as {resolved_id}"
    print(f"Aemeath state: {aemeath_state(sim)}")
    return resolved_id


def main() -> None:
    sim = Simulation.from_json(DATA_DIR)
    print(f"Initial Aemeath state: {aemeath_state(sim)}")

    run_step(sim, "swap_to_aemeath", "swap_to_aemeath")
    assert sim.state.active_character_id == "aemeath"

    run_step(sim, "aemeath_basic_attack", "aemeath_basic_form_stage_1")
    assert aemeath_state(sim)["aemeath_combo_stage"] == 2

    run_step(sim, "aemeath_resonance_skill", "aemeath_form_switch_to_mech")
    assert aemeath_state(sim)["form"] == "mech"

    run_step(sim, "aemeath_basic_attack", "aemeath_mech_basic_stage_2")

    sim.state.resonance_energy["aemeath"] = 125.0
    run_step(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    assert aemeath_state(sim)["seraphic_duo_remaining"] == 5.0
    assert aemeath_state(sim)["heavenfall_unbound"] is True

    before_seraphic_duet = aemeath_state(sim)["seraphic_duo_remaining"]
    run_step(sim, "aemeath_resonance_skill", "aemeath_seraphic_duet_overturn")
    after_seraphic_duet = aemeath_state(sim)["seraphic_duo_remaining"]
    assert after_seraphic_duet < before_seraphic_duet

    run_step(sim, "swap_to_main", "swap_to_main")
    after_swap_out = aemeath_state(sim)["seraphic_duo_remaining"]
    assert after_swap_out < after_seraphic_duet

    run_step(sim, "main_basic_attack", "main_basic_attack")
    after_off_field_action = aemeath_state(sim)["seraphic_duo_remaining"]
    assert after_off_field_action < after_swap_out

    run_step(sim, "swap_to_aemeath", "swap_to_aemeath")

    data = aemeath_state(sim)
    data["resonance_rate"] = 4.0
    print(f"Targeted resonance_rate setup for Finale check: {data}")

    run_step(sim, "aemeath_resonance_liberation", "aemeath_heavenfall_finale")
    final_state = aemeath_state(sim)
    assert final_state["form"] == "aemeath"
    assert final_state["synchronization_rate"] == 0.0
    assert final_state["resonance_rate"] == 0.0
    assert final_state["seraphic_duo_remaining"] == 0.0
    assert final_state["heavenfall_unbound"] is False
    assert final_state["finale_available"] is False
    assert final_state["aemeath_combo_stage"] == 1
    assert final_state["mech_combo_stage"] == 1

    print("Aemeath-lite smoke test passed.")


if __name__ == "__main__":
    main()
