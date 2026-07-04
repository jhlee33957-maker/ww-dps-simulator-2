from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"
BUFF_ID = "mornye_outro_recursion_all_dmg_amp"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def set_full_concerto(sim: Simulation, character_id: str) -> None:
    state = sim.state.character_states[character_id]
    ensure_concerto_state(state)
    state["concerto_energy"] = state["concerto_energy_cap"]
    state["concerto_ready"] = True
    sim.state.concerto_energy[character_id] = state["concerto_energy"]


def active_buff(sim: Simulation, buff_id: str):
    return next((buff for buff in sim.state.active_buffs if buff.buff_id == buff_id), None)


def first_aemeath_basic_damage() -> float:
    sim = Simulation.from_json(DATA_DIR, party="aemeath")
    assert sim.execute_action("aemeath_basic_attack")
    return sim.timeline[-1].total_action_damage


def main() -> None:
    baseline_damage = first_aemeath_basic_damage()

    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_test_party")
    assert sim.state.active_character_id == "mornye"
    assert "mornye_outro_recursion" not in sim.get_policy_action_ids()

    set_full_concerto(sim, "mornye")
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.outgoing_character_id == "mornye"
    assert row.incoming_character_id == "aemeath"
    assert row.transition_type == "full_concerto_transition"
    assert row.outgoing_outro_event_id == "mornye_outro_recursion"
    assert row.outgoing_outro_applied is True
    assert row.outgoing_concerto_consumed is True
    assert_close(row.outgoing_concerto_after, 0.0, "Mornye concerto after Outro")
    assert BUFF_ID in row.applied_buffs

    buff = active_buff(sim, BUFF_ID)
    assert buff is not None
    assert_close(buff.remaining_duration, 30.0, "Mornye Outro buff duration")
    buff_data = sim.buffs[BUFF_ID]
    assert buff_data.damage_amp_modifiers["all"] == 0.25
    assert buff_data.metadata["implementation_status"] == "implemented_v1"

    assert sim.execute_action("aemeath_basic_attack")
    damage_row = sim.timeline[-1]
    assert damage_row.total_action_damage > baseline_damage * 1.24
    assert BUFF_ID in damage_row.active_buffs

    print("Mornye Outro buff smoke test passed.")


if __name__ == "__main__":
    main()
