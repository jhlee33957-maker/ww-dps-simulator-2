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


def state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["aemeath"]


def derive(sim: Simulation) -> None:
    sim.character_mechanics["aemeath"].advance_time(sim.state, 0.0)


def execute(sim: Simulation, selected_action_id: str, expected_resolved_id: str) -> None:
    resolved_id = sim.resolve_action_id(selected_action_id)
    assert resolved_id == expected_resolved_id, f"{selected_action_id}: expected {expected_resolved_id}, got {resolved_id}"
    assert sim.execute_action(selected_action_id), f"Failed to execute {selected_action_id} resolved as {resolved_id}"


def prepare_overdrive(sim: Simulation, sync: float = 0.0, resonance_rate: float = 0.0) -> None:
    sim.state.resonance_energy["aemeath"] = 125.0
    data = state(sim)
    data["synchronization_rate"] = sync
    data["resonance_rate"] = resonance_rate


def test_overdrive() -> None:
    sim = make_sim()
    prepare_overdrive(sim)
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    data = state(sim)
    assert data["seraphic_duo_remaining"] == 0.0
    assert data["synchronization_rate"] == 30.0
    assert data["resonance_rate"] == 1.0
    assert data["heavenfall_unbound"] is True
    assert data["heavenfall_unbound_remaining"] == 60.0
    assert data["stardust_resonance_remaining"] == 30.0
    assert data["form"] == "mech"
    assert data["mech_combo_stage"] == 2

    sim = make_sim()
    prepare_overdrive(sim, sync=180.0)
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    assert state(sim)["synchronization_rate"] == 200.0


def test_overdrive_with_starlume_acceleration() -> None:
    sim = make_sim()
    prepare_overdrive(sim)
    state(sim)["starlume_acceleration_remaining"] = 5.0
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    assert state(sim)["resonance_rate"] == 2.0
    assert state(sim)["starlume_acceleration_remaining"] > 0.0

    sim = make_sim()
    prepare_overdrive(sim, resonance_rate=3.0)
    state(sim)["starlume_acceleration_remaining"] = 5.0
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    assert state(sim)["resonance_rate"] == 4.0


def test_instant_response() -> None:
    sim = make_sim()
    data = state(sim)
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["resonance_rate"] = 3.0
    execute(sim, "short_wait", "short_wait")
    assert state(sim)["instant_response"] is False

    sim = make_sim()
    data = state(sim)
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["resonance_rate"] = 4.0
    execute(sim, "short_wait", "short_wait")
    assert state(sim)["instant_response"] is True

    data = state(sim)
    data["heavenfall_unbound_remaining"] = 0.1
    execute(sim, "short_wait", "short_wait")
    assert state(sim)["heavenfall_unbound"] is False
    assert state(sim)["instant_response"] is False

    sim = make_sim()
    data = state(sim)
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["stardust_resonance_remaining"] = 30.0
    data["synchronization_rate"] = 200.0
    data["resonance_rate"] = 4.0
    derive(sim)
    execute(sim, "aemeath_resonance_liberation", "aemeath_heavenfall_finale")
    assert state(sim)["instant_response"] is False
    assert state(sim)["heavenfall_unbound"] is False
    assert state(sim)["synchronization_rate"] == 0.0
    assert state(sim)["resonance_rate"] == 0.0


def test_finale_replacement() -> None:
    sim = make_sim()
    prepare_overdrive(sim)
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_liberation_overdrive"

    sim = make_sim()
    data = state(sim)
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["resonance_rate"] = 0.0
    data["synchronization_rate"] = 0.0
    derive(sim)
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_heavenfall_finale"
    assert not sim.is_action_available(sim.actions["aemeath_resonance_liberation"])

    data["synchronization_rate"] = 200.0
    data["resonance_rate"] = 4.0
    derive(sim)
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_heavenfall_finale"
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_heavenfall_finale"
    assert sim.is_action_available(sim.actions["aemeath_resonance_liberation"])

    sim = make_sim()
    data = state(sim)
    data["resonance_rate"] = 4.0
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_liberation_overdrive"


def test_seraphic_duet_low_sync_behavior() -> None:
    sim = make_sim()
    data = state(sim)
    data["form"] = "aemeath"
    data["seraphic_duo_remaining"] = 5.0
    data["synchronization_rate"] = 99.0
    execute(sim, "aemeath_resonance_skill", "aemeath_form_switch_to_mech_normal")
    data = state(sim)
    assert data["seraphic_duo_remaining"] > 0.0
    assert data["form"] == "mech"
    assert data["mech_combo_stage"] == 2

    sim = make_sim()
    data = state(sim)
    data["form"] = "mech"
    data["seraphic_duo_remaining"] = 5.0
    data["synchronization_rate"] = 99.0
    execute(sim, "aemeath_resonance_skill", "aemeath_form_switch_to_aemeath_normal")
    data = state(sim)
    assert data["seraphic_duo_remaining"] > 0.0
    assert data["form"] == "aemeath"
    assert data["aemeath_combo_stage"] == 2


def test_seraphic_duet_high_sync_behavior() -> None:
    sim = make_sim()
    data = state(sim)
    data["form"] = "aemeath"
    data["seraphic_duo_remaining"] = 5.0
    data["synchronization_rate"] = 100.0
    execute(sim, "aemeath_resonance_skill", "aemeath_seraphic_duet_overturn")
    data = state(sim)
    assert data["seraphic_duo_remaining"] == 0.0
    assert data["synchronization_rate"] == 0.0
    assert data["resonance_rate"] == 1.0
    assert data["form"] == "mech"
    assert data["mech_combo_stage"] == 2

    sim = make_sim()
    data = state(sim)
    data["form"] = "mech"
    data["seraphic_duo_remaining"] = 5.0
    data["synchronization_rate"] = 100.0
    execute(sim, "aemeath_resonance_skill", "aemeath_seraphic_duet_encore")
    data = state(sim)
    assert data["seraphic_duo_remaining"] == 0.0
    assert data["synchronization_rate"] == 0.0
    assert data["resonance_rate"] == 1.0
    assert data["form"] == "aemeath"
    assert data["aemeath_combo_stage"] == 2


def test_overdrive_then_resonance_skill_is_normal_switch() -> None:
    sim = make_sim()
    prepare_overdrive(sim)
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    execute(sim, "aemeath_resonance_skill", "aemeath_form_switch_to_aemeath_normal")
    data = state(sim)
    assert data["seraphic_duo_remaining"] == 0.0
    assert data["form"] == "aemeath"
    assert data["aemeath_combo_stage"] == 2


def main() -> None:
    test_overdrive()
    test_overdrive_with_starlume_acceleration()
    test_instant_response()
    test_finale_replacement()
    test_seraphic_duet_low_sync_behavior()
    test_seraphic_duet_high_sync_behavior()
    test_overdrive_then_resonance_skill_is_normal_switch()
    print("Aemeath client mechanics smoke test passed.")


if __name__ == "__main__":
    main()
