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


def set_unbound(sim: Simulation, *, form: str, sync: float, resonance_rate: float, instant_response: bool) -> None:
    data = state(sim)
    data["form"] = form
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["synchronization_rate"] = sync
    data["resonance_rate"] = resonance_rate
    data["instant_response"] = instant_response
    data["instant_response_consumed"] = False


def multipliers(sim: Simulation, action_id: str) -> list[float]:
    return [hit.damage_multiplier for hit in sim.actions[action_id].hits]


def test_normal_form_switch_is_not_sync_strike() -> None:
    sim = make_sim()
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_form_switch_to_mech_normal"
    assert sim.resolve_action_id("aemeath_resonance_skill") != "aemeath_sync_strike_armament_merge"
    assert multipliers(sim, "aemeath_form_switch_to_mech_normal") == [0.696]
    assert multipliers(sim, "aemeath_form_switch_to_mech_normal") != multipliers(sim, "aemeath_sync_strike_armament_merge")


def test_human_basic_stage_2_opens_armament_merge() -> None:
    sim = make_sim()
    data = state(sim)
    data["form"] = "aemeath"
    data["aemeath_combo_stage"] = 2
    execute(sim, "aemeath_basic_attack", "aemeath_basic_form_stage_2")
    assert state(sim)["sync_strike_window_type"] == "armament_merge"
    execute(sim, "aemeath_resonance_skill", "aemeath_sync_strike_armament_merge")
    assert state(sim)["form"] == "mech"
    assert state(sim)["mech_combo_stage"] == 2


def test_mech_basic_stage_2_opens_call_of_dawn() -> None:
    sim = make_sim()
    data = state(sim)
    data["form"] = "mech"
    data["mech_combo_stage"] = 2
    execute(sim, "aemeath_basic_attack", "aemeath_mech_basic_stage_2")
    assert state(sim)["sync_strike_window_type"] == "call_of_dawn"
    execute(sim, "aemeath_resonance_skill", "aemeath_sync_strike_call_of_dawn")
    assert state(sim)["form"] == "aemeath"
    assert state(sim)["aemeath_combo_stage"] == 2


def test_human_heavy_charged_1() -> None:
    sim = make_sim()
    state(sim)["form"] = "aemeath"
    state(sim)["instant_response"] = False
    execute(sim, "aemeath_heavy_attack", "aemeath_heavy_aemeath_charged_1")
    assert state(sim)["aemeath_combo_stage"] == 2
    assert state(sim)["sync_strike_window_type"] == "armament_merge"


def test_human_heavy_charged_2_instant_response() -> None:
    sim = make_sim()
    set_unbound(sim, form="aemeath", sync=20.0, resonance_rate=4.0, instant_response=True)
    execute(sim, "aemeath_heavy_attack", "aemeath_heavy_aemeath_charged_2")
    data = state(sim)
    assert data["synchronization_rate"] == 200.0
    assert data["instant_response"] is False
    assert data["instant_response_consumed"] is True
    assert data["aemeath_combo_stage"] == 3
    assert data["sync_strike_window_type"] == "armament_merge"


def test_mech_heavy_charged_2_instant_response() -> None:
    sim = make_sim()
    set_unbound(sim, form="mech", sync=20.0, resonance_rate=4.0, instant_response=True)
    execute(sim, "aemeath_heavy_attack", "aemeath_heavy_mech_charged_2")
    data = state(sim)
    assert data["synchronization_rate"] == 200.0
    assert data["instant_response"] is False
    assert data["instant_response_consumed"] is True
    assert data["mech_combo_stage"] == 3
    assert data["sync_strike_window_type"] == "call_of_dawn"


def test_finale_after_instant_response_heavy() -> None:
    sim = make_sim()
    set_unbound(sim, form="aemeath", sync=20.0, resonance_rate=4.0, instant_response=True)
    execute(sim, "aemeath_heavy_attack", "aemeath_heavy_aemeath_charged_2")
    assert state(sim)["synchronization_rate"] == 200.0
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_heavenfall_finale"
    execute(sim, "aemeath_resonance_liberation", "aemeath_heavenfall_finale")
    data = state(sim)
    assert data["synchronization_rate"] == 0.0
    assert data["resonance_rate"] == 0.0
    assert data["heavenfall_unbound"] is False


def test_seraphic_duet_priority_over_sync_strike() -> None:
    sim = make_sim()
    data = state(sim)
    data["form"] = "aemeath"
    data["seraphic_duo_remaining"] = 5.0
    data["synchronization_rate"] = 100.0
    data["sync_strike_window_type"] = "armament_merge"
    data["sync_strike_window_remaining"] = 1
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_seraphic_duet_overturn"


def test_finale_priority_over_everything() -> None:
    sim = make_sim()
    set_unbound(sim, form="aemeath", sync=200.0, resonance_rate=4.0, instant_response=True)
    data = state(sim)
    data["seraphic_duo_remaining"] = 5.0
    data["sync_strike_window_type"] = "armament_merge"
    data["sync_strike_window_remaining"] = 1
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_heavenfall_finale"


def main() -> None:
    test_normal_form_switch_is_not_sync_strike()
    test_human_basic_stage_2_opens_armament_merge()
    test_mech_basic_stage_2_opens_call_of_dawn()
    test_human_heavy_charged_1()
    test_human_heavy_charged_2_instant_response()
    test_mech_heavy_charged_2_instant_response()
    test_finale_after_instant_response_heavy()
    test_seraphic_duet_priority_over_sync_strike()
    test_finale_priority_over_everything()
    print("Aemeath heavy and sync strike smoke test passed.")


if __name__ == "__main__":
    main()
