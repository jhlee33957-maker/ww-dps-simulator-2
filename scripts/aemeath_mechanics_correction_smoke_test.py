from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def make_sim() -> Simulation:
    return Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])


def aemeath_state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["aemeath"]


def derive(sim: Simulation) -> None:
    sim.character_mechanics["aemeath"].advance_time(sim.state, 0.0)


def execute(sim: Simulation, selected_action_id: str, expected_resolved_id: str) -> None:
    resolved_id = sim.resolve_action_id(selected_action_id)
    assert resolved_id == expected_resolved_id, f"{selected_action_id}: expected {expected_resolved_id}, got {resolved_id}"
    assert sim.execute_action(selected_action_id), f"Failed to execute {selected_action_id} resolved as {resolved_id}"


def test_basic_stage_4_grants_seraphic_duo() -> None:
    sim = make_sim()
    for expected_stage in range(1, 5):
        execute(sim, "aemeath_basic_attack", f"aemeath_basic_form_stage_{expected_stage}")
    state = aemeath_state(sim)
    assert state["seraphic_duo_remaining"] == 5.0

    sim = make_sim()
    state = aemeath_state(sim)
    state["form"] = "mech"
    for expected_stage in range(1, 5):
        execute(sim, "aemeath_basic_attack", f"aemeath_mech_basic_stage_{expected_stage}")
    state = aemeath_state(sim)
    assert state["seraphic_duo_remaining"] == 5.0


def test_overdrive_starts_timers_without_seraphic_duo() -> None:
    sim = make_sim()
    sim.state.resonance_energy["aemeath"] = 125.0
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    state = aemeath_state(sim)
    assert state["seraphic_duo_remaining"] == 0.0
    assert state["heavenfall_unbound"] is True
    assert state["heavenfall_unbound_remaining"] == 60.0
    assert state["stardust_resonance_remaining"] == 30.0
    assert state["synchronization_rate"] == 30.0
    assert state["resonance_rate"] == 1.0


def test_seraphic_duet_consumes_sync_and_switches_form() -> None:
    sim = make_sim()
    state = aemeath_state(sim)
    state["seraphic_duo_remaining"] = 5.0
    state["synchronization_rate"] = 150.0
    state["form"] = "aemeath"
    execute(sim, "aemeath_resonance_skill", "aemeath_seraphic_duet_overturn")
    state = aemeath_state(sim)
    assert state["synchronization_rate"] == 50.0
    assert state["seraphic_duo_remaining"] == 0.0
    assert state["form"] == "mech"
    assert state["mech_combo_stage"] == 2
    assert state["resonance_rate"] == 1.0

    sim = make_sim()
    state = aemeath_state(sim)
    state["seraphic_duo_remaining"] = 5.0
    state["synchronization_rate"] = 150.0
    state["form"] = "mech"
    execute(sim, "aemeath_resonance_skill", "aemeath_seraphic_duet_encore")
    state = aemeath_state(sim)
    assert state["synchronization_rate"] == 50.0
    assert state["seraphic_duo_remaining"] == 0.0
    assert state["form"] == "aemeath"
    assert state["aemeath_combo_stage"] == 2
    assert state["resonance_rate"] == 1.0


def test_finale_replaces_overdrive_during_heavenfall_unbound() -> None:
    sim = make_sim()
    sim.state.resonance_energy["aemeath"] = 125.0
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_liberation_overdrive"

    sim = make_sim()
    state = aemeath_state(sim)
    state["heavenfall_unbound"] = True
    state["heavenfall_unbound_remaining"] = 60.0
    state["synchronization_rate"] = 0.0
    state["resonance_rate"] = 0.0
    derive(sim)
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_heavenfall_finale"
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_form_switch_to_mech_normal"
    assert not sim.is_action_available(sim.actions["aemeath_resonance_liberation"])

    sim = make_sim()
    state = aemeath_state(sim)
    state["resonance_rate"] = 4.0
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_liberation_overdrive"

    sim = make_sim()
    state = aemeath_state(sim)
    state["heavenfall_unbound"] = True
    state["heavenfall_unbound_remaining"] = 60.0
    state["stardust_resonance_remaining"] = 30.0
    state["synchronization_rate"] = 200.0
    state["resonance_rate"] = 4.0
    derive(sim)
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_heavenfall_finale"
    execute(sim, "aemeath_resonance_liberation", "aemeath_heavenfall_finale")
    state = aemeath_state(sim)
    assert state["synchronization_rate"] == 0.0
    assert state["resonance_rate"] == 0.0
    assert state["heavenfall_unbound"] is False
    assert state["heavenfall_unbound_remaining"] == 0.0
    assert state["stardust_resonance_remaining"] == 0.0
    assert state["instant_response"] is False
    assert state["finale_available"] is False


def main() -> None:
    test_basic_stage_4_grants_seraphic_duo()
    test_overdrive_starts_timers_without_seraphic_duo()
    test_seraphic_duet_consumes_sync_and_switches_form()
    test_finale_replaces_overdrive_during_heavenfall_unbound()
    print("Aemeath mechanics correction smoke test passed.")


if __name__ == "__main__":
    main()
