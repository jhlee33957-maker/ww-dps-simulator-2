from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.action_executor import cooldown_key, reduce_cooldowns
from simulator.models import CombatState
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def approx(actual: float, expected: float, tolerance: float = 1e-4) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def assert_approx(actual: float, expected: float, label: str) -> None:
    assert approx(actual, expected), f"{label} expected {expected}, got {actual}"


def make_sim() -> Simulation:
    return Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])


def state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["aemeath"]


def set_finale_ready(sim: Simulation) -> None:
    data = state(sim)
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["synchronization_rate"] = 200.0
    data["resonance_rate"] = 4.0
    sim.character_mechanics["aemeath"].advance_time(sim.state, 0.0)


def execute(sim: Simulation, action_id: str, expected_resolved_id: str) -> None:
    resolved_id = sim.resolve_action_id(action_id)
    assert resolved_id == expected_resolved_id, f"{action_id}: expected {expected_resolved_id}, got {resolved_id}"
    assert sim.execute_action(action_id), f"Failed to execute {action_id} resolved as {resolved_id}"


def test_reduce_cooldowns_helper() -> None:
    combat_state = CombatState(active_character_id="aemeath")
    combat_state.cooldowns["probe"] = 25.0
    reduce_cooldowns(combat_state, 0.0)
    assert_approx(combat_state.cooldowns["probe"], 25.0, "zero-combat cooldown tick")
    reduce_cooldowns(combat_state, 1.0)
    assert_approx(combat_state.cooldowns["probe"], 24.0, "one-second cooldown tick")


def test_overdrive_and_finale_do_not_tick_existing_cooldowns() -> None:
    sim = make_sim()
    overdrive = sim.actions["aemeath_liberation_overdrive"]
    assert_approx(overdrive.action_time or 0.0, 4.3667, "Overdrive action_time")
    assert_approx(overdrive.combat_time_cost or 0.0, 0.0, "Overdrive combat_time_cost")
    sim.state.resonance_energy["aemeath"] = 125.0
    sim.state.cooldowns["probe"] = 25.0
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    assert_approx(sim.state.cooldowns["probe"], 25.0, "Overdrive cinematic cooldown tick")

    sim = make_sim()
    finale = sim.actions["aemeath_heavenfall_finale"]
    assert_approx(finale.action_time or 0.0, 5.6667, "Finale action_time")
    assert_approx(finale.combat_time_cost or 0.0, 0.0, "Finale combat_time_cost")
    sim.state.cooldowns["probe"] = 25.0
    set_finale_ready(sim)
    execute(sim, "aemeath_resonance_liberation", "aemeath_heavenfall_finale")
    assert_approx(sim.state.cooldowns["probe"], 25.0, "Finale cinematic cooldown tick")


def test_seraphic_duet_ticks_by_combat_time_cost() -> None:
    sim = make_sim()
    sim.state.cooldowns["probe"] = 25.0
    data = state(sim)
    data["form"] = "aemeath"
    data["seraphic_duo_remaining"] = 5.0
    data["synchronization_rate"] = 100.0
    execute(sim, "aemeath_resonance_skill", "aemeath_seraphic_duet_overturn")
    assert_approx(sim.timeline[-1].action_time, 3.0, "Seraphic Overturn action_time")
    assert_approx(sim.timeline[-1].combat_time_cost, 1.3167, "Seraphic Overturn combat_time_cost")
    assert_approx(sim.state.cooldowns["probe"], 25.0 - 1.3167, "Seraphic Overturn cooldown tick")

    sim = make_sim()
    sim.state.cooldowns["probe"] = 25.0
    data = state(sim)
    data["form"] = "mech"
    data["seraphic_duo_remaining"] = 5.0
    data["synchronization_rate"] = 100.0
    execute(sim, "aemeath_resonance_skill", "aemeath_seraphic_duet_encore")
    assert_approx(sim.timeline[-1].action_time, 2.4167, "Seraphic Encore action_time")
    assert_approx(sim.timeline[-1].combat_time_cost, 1.3333, "Seraphic Encore combat_time_cost")
    assert_approx(sim.state.cooldowns["probe"], 25.0 - 1.3333, "Seraphic Encore cooldown tick")


def test_normal_action_fallback_ticks_by_action_time() -> None:
    sim = make_sim()
    basic = sim.actions["aemeath_basic_form_stage_1"]
    assert basic.combat_time_cost is None
    sim.state.cooldowns["probe"] = 25.0
    execute(sim, "aemeath_basic_attack", "aemeath_basic_form_stage_1")
    assert_approx(sim.timeline[-1].action_time, 0.45, "Basic fallback action_time")
    assert_approx(sim.timeline[-1].combat_time_cost, 0.45, "Basic fallback combat_time_cost")
    assert_approx(sim.state.cooldowns["probe"], 24.55, "Basic fallback cooldown tick")


def test_form_switch_group_ticks_by_combat_time_cost() -> None:
    sim = make_sim()
    form_switch = sim.actions["aemeath_form_switch_to_mech_normal"]
    assert cooldown_key(form_switch) == "aemeath_form_switch"
    execute(sim, "aemeath_resonance_skill", "aemeath_form_switch_to_mech_normal")
    assert_approx(sim.state.cooldowns["aemeath_form_switch"], 1.0, "Form Switch cooldown starts")

    execute(sim, "short_wait", "short_wait")
    assert_approx(sim.state.cooldowns["aemeath_form_switch"], 0.5, "Form Switch cooldown ticks by wait combat cost")

    sim = make_sim()
    sim.state.cooldowns["aemeath_form_switch"] = 1.0
    sim.state.resonance_energy["aemeath"] = 125.0
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    assert_approx(sim.state.cooldowns["aemeath_form_switch"], 1.0, "Form Switch cooldown ignores Overdrive action_time")


def test_cinematic_time_does_not_shortcut_25s_cooldown() -> None:
    sim = make_sim()
    sim.state.cooldowns["probe"] = 25.0
    sim.state.resonance_energy["aemeath"] = 125.0
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    assert_approx(sim.state.combat_time, 0.0, "Overdrive combat clock")
    assert_approx(sim.state.cooldowns["probe"], 25.0, "Cooldown after 0 combat seconds")

    for _ in range(37):
        execute(sim, "short_wait", "short_wait")
    assert_approx(sim.state.combat_time, 18.5, "Scripted 18.5 combat seconds")
    assert sim.state.cooldowns["probe"] > 0.0, "25s cooldown became available after only 18.5 combat seconds"
    assert_approx(sim.state.cooldowns["probe"], 6.5, "Remaining cooldown after 18.5 combat seconds")


def main() -> None:
    test_reduce_cooldowns_helper()
    test_overdrive_and_finale_do_not_tick_existing_cooldowns()
    test_seraphic_duet_ticks_by_combat_time_cost()
    test_normal_action_fallback_ticks_by_action_time()
    test_form_switch_group_ticks_by_combat_time_cost()
    test_cinematic_time_does_not_shortcut_25s_cooldown()
    print("Aemeath cooldown combat-time smoke test passed.")


if __name__ == "__main__":
    main()
